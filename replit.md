# YouTube API Service

## Overview

This is a Flask-based YouTube API service that provides music streaming capabilities with intelligent caching through Telegram. The service extracts 720p MP4 streams from YouTube content using the Clipto API and offers both direct streaming and cached delivery mechanisms. It features a comprehensive API key management system with rate limiting, admin controls, and usage analytics.

## Recent Changes

- **Admin Panel Enhanced (August 14, 2025)**: Created powerful professional admin panel with API key authentication (key=NOTTY_BOY)
- **Advanced UI/UX**: Implemented stunning 3D professional design with comprehensive NOTTY BOY branding throughout
- **Custom Daily Limits**: Added support for custom daily request limits up to 100 trillion per day
- **Enhanced Analytics**: Comprehensive statistics showing today/week/month requests, Telegram & API response tracking
- **Copy Functionality**: Added copy-to-clipboard features for API keys with visual feedback
- **Async Issues Resolved**: Fixed all event loop conflicts with new AdminHelper threading system
- **Migration Complete (August 14, 2025)**: Successfully migrated from Replit Agent to standard Replit environment
- **YouTube Handler Updated**: Replaced yt-dlp with Clipto API for reliable 720p MP4 extraction
- **Dependencies Fixed**: Corrected package names and resolved all import issues  
- **MongoDB Confirmed**: Using only MongoDB Atlas, no local or temporary databases

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Flask** with Blueprint architecture for modular route organization
- **Async/await patterns** using asyncio for concurrent operations
- **Rate limiting** via flask-limiter with IP-based throttling (100 requests/minute default)
- **Proxy-aware middleware** for proper IP detection behind reverse proxies

### Authentication & Authorization
- **API key-based authentication** with UUID generation
- **Two-tier access control**: Regular users (1,000 daily requests) and admin users (10M daily requests)  
- **Automatic expiration system** with configurable expiry periods (default 30 days)
- **Daily usage tracking** with automatic reset at Indian timezone midnight
- **Request logging** for audit trails and analytics

### Data Storage
- **MongoDB** as primary database using Motor async driver
- **Three main collections**:
  - `api_keys`: Stores API key metadata and usage statistics
  - `api_logs`: Tracks API usage for analytics and monitoring
  - `cache_metadata`: Manages cached content information
- **In-memory stream cache** for temporary URL storage with 24-hour TTL

### YouTube Processing Pipeline
- **Clipto API Integration**: Primary extraction using Clipto API for reliable 720p MP4 streams
- **Content identification**: Supports YouTube URLs, video IDs, and search queries  
- **720p Video Quality**: Focuses on high-quality MP4 streams with audio
- **Stream session management**: Temporary URLs with UUID-based session tracking
- **Migration Date**: August 14, 2025 - Migrated from yt-dlp to Clipto API for better reliability

### Caching Strategy
- **Telegram-based storage**: Uses Telegram channels as CDN for cached content
- **Pyrogram client integration** for file upload/download operations
- **Metadata persistence**: Cache entries stored in MongoDB with expiration tracking
- **Content deduplication**: Prevents redundant caching of identical content

### Admin Interface
- **Web-based dashboard** with Bootstrap dark theme
- **Real-time statistics**: API usage, key management, and error rate monitoring
- **Interactive charts** using Chart.js for usage visualization
- **Key lifecycle management**: Create, view, and manage API keys with custom limits

### Error Handling & Monitoring
- **Comprehensive logging** with colored console output and structured formatting
- **Error categorization**: HTTP status codes with detailed error messages
- **Health monitoring**: Built-in health check endpoints
- **Request tracking**: Response time measurement and endpoint usage analytics

## External Dependencies

### Core Services
- **MongoDB Atlas**: Cloud database for persistent storage via connection string
- **Telegram Bot API**: Content caching and delivery infrastructure
  - Bot token authentication
  - Channel-based file storage
  - Pyrogram client for advanced operations

### Python Libraries
- **Flask ecosystem**: Core web framework with limiter and proxy support
- **Motor**: Async MongoDB driver for non-blocking database operations  
- **Pyrogram**: Modern Telegram client for file operations
- **youtube-search-python**: YouTube search functionality for query resolution
- **Requests**: HTTP client for Clipto API integration

### Frontend Assets
- **Bootstrap 5**: UI framework with dark theme support
- **Font Awesome**: Icon library for enhanced user interface
- **Chart.js**: Data visualization for admin dashboard analytics

### Configuration Management
- **Environment variables**: Secure credential storage for API keys and tokens
- **Configurable limits**: Rate limiting and quota management through config module
- **Debug mode**: Development-friendly logging and error reporting