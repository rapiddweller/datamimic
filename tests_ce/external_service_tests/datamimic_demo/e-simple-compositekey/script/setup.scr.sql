-- IMPORTANT: Only use semicolon for commands split when using SQLite
-- Drop table if it exists
DROP TABLE IF EXISTS playlist;
DROP TABLE IF EXISTS TRACK;
DROP TABLE IF EXISTS PLAYLIST_TRACK;

-- Create playlist table
CREATE TABLE playlist (
    PLAYLIST_ID INTEGER NOT NULL,
    name TEXT NOT NULL,
    PRIMARY KEY (PLAYLIST_ID)
);

-- Create track table
CREATE TABLE TRACK (
    TRACK_ID INTEGER NOT NULL,
    name TEXT NOT NULL,
    PRIMARY KEY (TRACK_ID)
);

-- Create playlist_track table
CREATE TABLE PLAYLIST_TRACK (
    PLAYLIST_ID INTEGER NOT NULL,
    TRACK_ID INTEGER NOT NULL,
    name TEXT NOT NULL,
    UNIQUE (PLAYLIST_ID, TRACK_ID)
);
