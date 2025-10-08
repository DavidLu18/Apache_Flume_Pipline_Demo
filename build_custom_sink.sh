#!/bin/bash
# ====================================================================================
# Build Custom PostgreSQL Sink for Flume - Simplified
# ====================================================================================

set -e

echo "======================================================================"
echo "🔨 Building Custom PostgreSQL Sink for Apache Flume"
echo "======================================================================"

# Cấu hình
PROJECT_DIR="/home/david/Downloads/Apache_Flume_Demo"
CUSTOM_SINK_DIR="$PROJECT_DIR/custom-sink"
SRC_DIR="$CUSTOM_SINK_DIR/src/main/java"
FLUME_HOME="/opt/flume"
BUILD_DIR="$CUSTOM_SINK_DIR/target"
JAR_NAME="flume-postgresql-sink.jar"

# Kiểm tra JDK
if ! command -v javac &> /dev/null; then
    echo "❌ JDK not found. Please install JDK 8 or higher."
    echo "   Run: sudo apt install openjdk-11-jdk"
    exit 1
fi

echo "✓ Java compiler found"
java -version 2>&1 | head -1

# Tạo thư mục build
echo ""
echo "[1/4] Preparing build directory..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/classes"

# Build classpath - Use all Flume JARs
CLASSPATH="$FLUME_HOME/lib/*"

echo "✓ Using all Flume libraries from: $FLUME_HOME/lib/"

# Compile
echo ""
echo "[2/4] Compiling PostgreSQLSink.java..."
javac -d "$BUILD_DIR/classes" \
    -cp "$CLASSPATH" \
    -source 1.8 -target 1.8 \
    "$SRC_DIR/com/f1demo/flume/PostgreSQLSink.java"

if [ $? -ne 0 ]; then
    echo "❌ Compilation failed!"
    exit 1
fi

echo "✓ Compilation successful"

# Tạo JAR với dependencies (fat JAR)
echo ""
echo "[3/4] Creating fat JAR with dependencies..."
cd "$BUILD_DIR"
mkdir -p temp/META-INF

# Extract dependencies
cd temp
jar -xf "$FLUME_HOME/lib/gson-2.9.1.jar"
rm -rf META-INF/*.SF META-INF/*.DSA META-INF/*.RSA 2>/dev/null || true
jar -xf "$FLUME_HOME/lib/postgresql-42.7.3.jar"
rm -rf META-INF/*.SF META-INF/*.DSA META-INF/*.RSA 2>/dev/null || true

# Copy compiled classes
cp -r "$BUILD_DIR/classes/"* .

# Create JAR
jar -cf "$BUILD_DIR/$JAR_NAME" .

cd "$BUILD_DIR"
rm -rf temp classes

echo "✓ JAR created: $JAR_NAME ($(du -h $JAR_NAME | cut -f1))"

# Deploy vào Flume
echo ""
echo "[4/4] Deploying to Flume..."
sudo cp "$BUILD_DIR/$JAR_NAME" "$FLUME_HOME/lib/"

echo ""
echo "======================================================================"
echo "✅ BUILD THÀNH CÔNG!"
echo "======================================================================"
echo "📦 Deployed: $FLUME_HOME/lib/$JAR_NAME"
echo ""
echo "📋 Bước tiếp theo:"
echo "   1. Xem config: cat flume/flume-jdbc.conf"
echo "   2. Start Flume: ./start_flume_jdbc.sh"
echo "   3. Start Reddit streamer: ./start_streamer.sh"
echo "======================================================================"
