"""Arquivos locais em data/: candidates.json, ready.json, pushed.jsonl."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from affiliate_worker.models import Offer

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / 'data'


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


class Storage:
    def __init__(self, data_dir: str | Path | None = None):
        self.data_dir = Path(data_dir or os.environ.get('AFFILIATE_DATA_DIR') or DEFAULT_DATA_DIR)

    @property
    def candidates_path(self) -> Path:
        return self.data_dir / 'candidates.json'

    @property
    def ready_path(self) -> Path:
        return self.data_dir / 'ready.json'

    @property
    def pushed_path(self) -> Path:
        return self.data_dir / 'pushed.jsonl'

    def _ensure_dir(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _write_json(self, path: Path, data) -> None:
        self._ensure_dir()
        tmp = path.with_suffix(path.suffix + '.tmp')
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        tmp.replace(path)  # escrita atômica: não deixa arquivo pela metade

    def _read_offers(self, path: Path) -> list[Offer]:
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding='utf-8') or '{}')
        items = data.get('offers', []) if isinstance(data, dict) else data
        return [Offer.from_dict(item) for item in items]

    def save_candidates(self, offers: list[Offer]) -> None:
        self._write_json(self.candidates_path, {'offers': [o.to_dict() for o in offers]})

    def load_candidates(self) -> list[Offer]:
        return self._read_offers(self.candidates_path)

    def load_ready(self) -> list[Offer]:
        return self._read_offers(self.ready_path)

    def save_ready(self, offers: list[Offer]) -> None:
        self._write_json(self.ready_path, {'offers': [o.to_dict() for o in offers]})

    def merge_ready(self, incoming: list[Offer]) -> tuple[int, int]:
        """Mescla ofertas importadas em ready.json pela chave. Retorna (novas, atualizadas).

        Ao atualizar, campos preenchidos no import sobrescrevem; controle local de push é zerado
        para a oferta ser reenviada com os dados novos.
        """
        current = self.load_ready()
        index = {o.key(): i for i, o in enumerate(current)}
        added = updated = 0
        for offer in incoming:
            k = offer.key()
            if k in index:
                existing = current[index[k]]
                for name, value in offer.to_payload().items():
                    setattr(existing, name, value)
                existing.pushed_at = None
                updated += 1
            else:
                index[k] = len(current)
                current.append(offer)
                added += 1
        self.save_ready(current)
        return added, updated

    def append_pushed(self, record: dict) -> None:
        self._ensure_dir()
        record = {'at': now_iso(), **record}
        with self.pushed_path.open('a', encoding='utf-8') as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + '\n')
