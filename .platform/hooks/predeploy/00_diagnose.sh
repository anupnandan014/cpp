#!/bin/bash
echo "--- DIAGNOSTICS ---"
ls -la /var/app || echo "no /var/app"
echo "--- /tmp perms ---"
ls -la /tmp
echo "--- touch test ---"
touch /tmp/writetest.txt && echo "WRITE OK" && rm /tmp/writetest.txt
