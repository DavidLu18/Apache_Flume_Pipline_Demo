#!/bin/bash
# ====================================================================================
# Start Flume with Custom JDBC Sink
# ====================================================================================

FLUME_HOME="/opt/flume"
PROJECT_DIR="/home/david/Downloads/Apache_Flume_Demo"
CONFIG_FILE="$PROJECT_DIR/flume/flume-jdbc.conf"

echo "======================================================================"
echo "🚀 Starting Flume with Custom PostgreSQL JDBC Sink"
echo "======================================================================"

# Kiểm tra JAR đã được build chưa
if [ ! -f "$FLUME_HOME/lib/flume-postgresql-sink.jar" ]; then
    echo "❌ Custom sink JAR not found!"
    echo "   Please run: ./build_custom_sink.sh"
    exit 1
fi

echo "✓ Custom sink JAR found"

# Kiểm tra config file
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Config file not found: $CONFIG_FILE"
    exit 1
fi

echo "✓ Config file: flume/flume-jdbc.conf"

# Stop Flume nếu đang chạy
echo ""
echo "Stopping existing Flume processes..."
pkill -f "flume-ng" 2>/dev/null || true
sleep 2

# Start Flume
echo ""
echo "Starting Flume agent..."
echo "======================================================================"

cd "$PROJECT_DIR"

nohup $FLUME_HOME/bin/flume-ng agent \
    --conf $FLUME_HOME/conf \
    --conf-file $CONFIG_FILE \
    --name a1 \
    -Dflume.root.logger=INFO,console \
    > flume-jdbc.log 2>&1 &

FLUME_PID=$!

sleep 3

# Kiểm tra Flume có chạy không
if ps -p $FLUME_PID > /dev/null; then
    echo ""
    echo "✅ Flume started successfully!"
    echo "   PID: $FLUME_PID"
    echo "   Log: tail -f flume-jdbc.log"
    echo ""
    echo "📡 Listening on port 44444 for Reddit data"
    echo "======================================================================"
else
    echo ""
    echo "❌ Flume failed to start. Check log:"
    echo "   tail -f flume-jdbc.log"
    exit 1
fi
