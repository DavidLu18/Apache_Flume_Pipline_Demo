package com.f1demo.flume;

import org.apache.flume.*;
import org.apache.flume.conf.Configurable;
import org.apache.flume.sink.AbstractSink;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.sql.*;

/**
 * Custom Flume Sink for PostgreSQL
 * Giải pháp production để sink data trực tiếp vào PostgreSQL
 */
public class PostgreSQLSink extends AbstractSink implements Configurable {
    
    private String jdbcUrl;
    private String username;
    private String password;
    private Connection connection;
    
    @Override
    public void configure(Context context) {
        // Đọc config từ flume.conf
        jdbcUrl = context.getString("jdbcUrl", "jdbc:postgresql://localhost:5432/mydb");
        username = context.getString("username", "postgres");
        password = context.getString("password", "postgres123");
    }
    
    @Override
    public void start() {
        super.start();
        try {
            // Kết nối PostgreSQL
            connection = DriverManager.getConnection(jdbcUrl, username, password);
            connection.setAutoCommit(true); // IMPORTANT: Enable auto-commit for each statement
            System.out.println("✓ PostgreSQL Sink started successfully");
        } catch (SQLException e) {
            throw new RuntimeException("Failed to connect to PostgreSQL", e);
        }
    }
    
    @Override
    public Status process() throws EventDeliveryException {
        Status status = Status.READY;
        Channel channel = getChannel();
        Transaction txn = channel.getTransaction();
        
        try {
            txn.begin();
            Event event = channel.take();
            
            if (event == null) {
                status = Status.BACKOFF;
            } else {
                // Parse JSON event
                String body = new String(event.getBody(), "UTF-8");
                JsonObject json = JsonParser.parseString(body).getAsJsonObject();
                
                String type = json.get("type").getAsString();
                
                if ("post".equals(type)) {
                    insertPost(json);
                } else if ("comment".equals(type)) {
                    insertComment(json);
                }
                
                status = Status.READY;
            }
            
            txn.commit();
        } catch (Exception e) {
            txn.rollback();
            throw new EventDeliveryException("Failed to process event", e);
        } finally {
            txn.close();
        }
        
        return status;
    }
    
    private void insertPost(JsonObject data) throws SQLException {
        String sql = "INSERT INTO posts (id, title, content, score, flair, created_utc, subreddit) " +
                     "VALUES (?, ?, ?, ?, ?, ?::timestamp, ?) " +
                     "ON CONFLICT (id) DO UPDATE SET score = EXCLUDED.score, flair = EXCLUDED.flair";
        
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setString(1, data.get("id").getAsString());
            stmt.setString(2, data.get("title").getAsString());
            stmt.setString(3, data.get("content").getAsString());
            stmt.setInt(4, data.get("score").getAsInt());
            stmt.setString(5, data.get("flair").getAsString());
            stmt.setString(6, data.get("created_utc").getAsString());
            stmt.setString(7, data.get("subreddit").getAsString());
            stmt.executeUpdate();
            
            System.out.println("✓ Inserted post: " + data.get("id").getAsString());
        }
    }
    
    private void insertComment(JsonObject data) throws SQLException {
        String sql = "INSERT INTO comments (id, post_id, content, score, created_utc, author) " +
                     "VALUES (?, ?, ?, ?, ?::timestamp, ?) " +
                     "ON CONFLICT (id) DO UPDATE SET score = EXCLUDED.score";
        
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setString(1, data.get("id").getAsString());
            stmt.setString(2, data.get("post_id").getAsString());
            stmt.setString(3, data.get("content").getAsString());
            stmt.setInt(4, data.get("score").getAsInt());
            stmt.setString(5, data.get("created_utc").getAsString());
            stmt.setString(6, data.get("author").getAsString());
            stmt.executeUpdate();
            
            System.out.println("✓ Inserted comment: " + data.get("id").getAsString());
        }
    }
    
    @Override
    public void stop() {
        try {
            if (connection != null && !connection.isClosed()) {
                connection.close();
            }
        } catch (SQLException e) {
            System.err.println("Error closing connection: " + e.getMessage());
        }
        super.stop();
    }
}
