`postAction` em `active-window-table.tsx` tipava o payload como `Record<string, unknown>` e quebrava `tsc --noEmit` (único erro de tipo do painel)
