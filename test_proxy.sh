#!/bin/bash
# Test script to verify marionette proxy works

set -e

echo "=== Killing any existing processes ==="
pkill -f "marionette_client|marionette_server|socksserver" || true
sleep 1

echo "=== Starting SOCKS server ==="
python3 examples/socksserver --local_port 8081 > /tmp/socksserver.log 2>&1 &
SOCKS_PID=$!
sleep 1

echo "=== Starting marionette_server ==="
python3 bin/marionette_server --server_ip 127.0.0.1 --proxy_ip 127.0.0.1 --proxy_port 8081 --format dummy --debug > /tmp/marionette_server.log 2>&1 &
SERVER_PID=$!
sleep 1

echo "=== Starting marionette_client ==="
python3 bin/marionette_client --server_ip 127.0.0.1 --client_ip 127.0.0.1 --client_port 8079 --format dummy --debug > /tmp/marionette_client.log 2>&1 &
CLIENT_PID=$!
sleep 2

echo "=== Testing direct SOCKS connection ==="
curl --socks4a 127.0.0.1:8081 -m 5 http://example.com > /dev/null 2>&1 && echo "✓ Direct SOCKS works" || echo "✗ Direct SOCKS failed"

echo "=== Testing marionette proxy ==="
curl --socks4a 127.0.0.1:8079 -m 10 http://example.com > /tmp/curl_output.html 2>&1
if [ $? -eq 0 ] && grep -q "Example Domain" /tmp/curl_output.html; then
    echo "✓ Marionette proxy works!"
    echo "Response preview:"
    head -3 /tmp/curl_output.html
else
    echo "✗ Marionette proxy failed"
    echo "Client log (last 20 lines):"
    tail -20 /tmp/marionette_client.log
    echo ""
    echo "Server log (last 20 lines):"
    tail -20 /tmp/marionette_server.log
fi

echo ""
echo "=== Cleaning up ==="
kill $CLIENT_PID $SERVER_PID $SOCKS_PID 2>/dev/null || true
