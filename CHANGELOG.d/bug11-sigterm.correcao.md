**Container honra SIGTERM** — o handler só sinaliza e o daemon sai em até 8s com código 0, em vez de `docker stop` virar SIGKILL (bug 11)
