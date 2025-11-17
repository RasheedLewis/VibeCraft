# Unit Tests Overview

This document provides a comprehensive overview of all unit tests for Phases 1 and 2: Authentication and Audio Upload & Storage.

## Test Structure

All unit tests are located in `v2/backend/tests/unit/` and follow these principles:
- **Fast**: Run in ~0.1-0.2s each, no external dependencies
- **Isolated**: Mock all external services (S3, database, ffprobe)
- **Focused**: Test single units of functionality
- **Comprehensive**: Cover success paths, error cases, and edge cases

## Test Files

### Phase 1: Authentication Tests

#### 1. `test_user_model.py` (15 tests)

Tests the User model password hashing and verification - critical security functionality.

**Why these tests matter**: Password security is the foundation of authentication. Bugs here compromise all user accounts.

#### Password Hashing (7 tests)
- ✅ `test_hash_password_valid` - Validates password hashing produces bcrypt hash
- ✅ `test_hash_password_different_passwords_different_hashes` - Different passwords produce different hashes
- ✅ `test_hash_password_same_password_different_hashes` - Same password produces different hashes (salt)
- ✅ `test_hash_password_long_password` - Handles passwords > 72 bytes (bcrypt limit, truncates)
- ✅ `test_hash_password_unicode` - Handles unicode/emoji passwords
- ✅ `test_hash_password_emoji` - Handles emoji characters in passwords
- ✅ `test_hash_password_empty` - Handles empty password

#### Password Verification (8 tests)
- ✅ `test_verify_password_correct` - Validates correct password verification
- ✅ `test_verify_password_incorrect` - Rejects wrong passwords
- ✅ `test_verify_password_case_sensitive` - Validates case-sensitive password matching
- ✅ `test_verify_password_empty_wrong` - Rejects empty password against non-empty hash
- ✅ `test_verify_password_long_password` - Handles long password verification (truncation)
- ✅ `test_verify_password_unicode` - Handles unicode password verification
- ✅ `test_verify_password_emoji` - Handles emoji password verification
- ✅ `test_verify_password_special_characters` - Handles special characters in passwords

---

#### 2. `test_auth_service.py` (19 tests)

Tests authentication service: JWT token creation/verification, user registration, and authentication.

**Why these tests matter**: JWT token security and user authentication logic. Bugs here allow unauthorized access.

#### JWT Token Creation (3 tests)
- ✅ `test_create_access_token_success` - Validates token generation with correct user_id
- ✅ `test_create_access_token_different_users` - Different users get different tokens
- ✅ `test_create_access_token_expiration` - Validates token expiration (7 days)

#### JWT Token Verification (7 tests)
- ✅ `test_verify_token_valid` - Validates successful token verification
- ✅ `test_verify_token_expired` - Rejects expired tokens
- ✅ `test_verify_token_invalid_format` - Rejects invalid token format
- ✅ `test_verify_token_tampered` - Rejects tampered tokens
- ✅ `test_verify_token_wrong_secret` - Rejects tokens with wrong secret key
- ✅ `test_verify_token_missing_sub` - Rejects tokens without 'sub' claim
- ✅ `test_verify_token_none_sub` - Rejects tokens with None 'sub' claim

#### User Registration (3 tests)
- ✅ `test_register_user_success` - Validates successful user registration
- ✅ `test_register_user_duplicate_email` - Rejects duplicate email registration
- ✅ `test_register_user_password_hashed` - Validates password is hashed (not plaintext)

#### User Authentication (4 tests)
- ✅ `test_authenticate_user_success` - Validates successful authentication
- ✅ `test_authenticate_user_invalid_email` - Rejects non-existent email
- ✅ `test_authenticate_user_invalid_password` - Rejects wrong password
- ✅ `test_authenticate_user_case_sensitive_email` - Validates case-sensitive email matching

#### User Lookup (2 tests)
- ✅ `test_get_user_by_id_success` - Validates successful user lookup
- ✅ `test_get_user_by_id_not_found` - Handles non-existent user ID

---

#### 3. `test_auth_deps.py` (6 tests)

Tests authentication dependencies, specifically `get_current_user` for protected routes.

**Why these tests matter**: Token extraction and validation in protected routes. Bugs here bypass authentication.

#### get_current_user Dependency (6 tests)
- ✅ `test_get_current_user_success` - Validates successful user retrieval with valid token
- ✅ `test_get_current_user_invalid_token` - Rejects invalid tokens (401)
- ✅ `test_get_current_user_expired_token` - Rejects expired tokens (401)
- ✅ `test_get_current_user_user_not_found` - Handles valid token but user not found (401)
- ✅ `test_get_current_user_tampered_token` - Rejects tampered tokens (401)
- ✅ `test_get_current_user_correct_user_returned` - Validates correct user is returned based on token

---

### Phase 2: Audio Upload & Storage Tests

#### 4. `test_audio_validation.py` (20 tests)

Tests the audio file validation service that checks file format, size, and duration.

#### Format Validation (8 tests)
- ✅ `test_valid_mp3` - Validates MP3 files are accepted
- ✅ `test_valid_wav` - Validates WAV files are accepted
- ✅ `test_valid_m4a` - Validates M4A files are accepted
- ✅ `test_invalid_format_txt` - Rejects non-audio files (text)
- ✅ `test_invalid_format_pdf` - Rejects non-audio files (PDF)
- ✅ `test_invalid_format_no_extension` - Handles missing file extension
- ✅ `test_case_insensitive_extension` - Ensures `.MP3` works (case-insensitive)
- ✅ `test_special_characters_in_filename` - Handles real-world filenames with special chars

#### File Size Validation (4 tests)
- ✅ `test_valid_size_under_limit` - Validates files under 50MB limit
- ✅ `test_valid_size_at_limit` - Validates boundary case (exactly 50MB)
- ✅ `test_invalid_size_over_limit` - Rejects files over 50MB
- ✅ `test_empty_file` - Rejects empty files

#### Duration Validation (4 tests)
- ✅ `test_valid_duration_under_limit` - Validates durations under 5 minute limit
- ✅ `test_valid_duration_at_limit` - Validates boundary case (exactly 5 minutes)
- ✅ `test_invalid_duration_over_limit` - Rejects durations over 5 minutes
- ✅ `test_invalid_duration_zero` - Rejects zero duration
- ✅ `test_invalid_duration_negative` - Rejects negative duration

#### ffprobe Integration (4 tests)
- ✅ `test_ffprobe_success` - Validates successful ffprobe execution
- ✅ `test_ffprobe_failure` - Handles ffprobe errors gracefully
- ✅ `test_ffprobe_no_duration` - Handles missing duration output
- ✅ `test_ffprobe_exception_handling` - Handles exceptions during ffprobe execution

#### Edge Cases (4 tests)
- ✅ `test_missing_filename` - Handles empty filename gracefully
- ✅ `test_very_long_filename` - Handles extremely long filenames
- ✅ `test_multiple_dots_in_filename` - Validates extension extraction with multiple dots
- ✅ `test_unicode_filename` - Handles Unicode characters in filenames

**Why these tests matter**: Audio validation is the first line of defense against invalid uploads. These tests ensure we catch format, size, and duration issues before they reach S3 or the database.

---

#### 5. `test_storage_service.py` (13 tests)

Tests S3 storage operations with mocked boto3 client.

#### Upload Operations (4 tests)
- ✅ `test_upload_success_without_content_type` - Validates upload without content type
- ✅ `test_upload_success_with_content_type` - Validates upload with content type
- ✅ `test_upload_failure_boto_error` - Handles BotoCoreError exceptions
- ✅ `test_upload_failure_client_error` - Handles ClientError exceptions (different error type)

#### Download Operations (3 tests)
- ✅ `test_download_success` - Validates successful file download
- ✅ `test_download_failure_boto_error` - Handles download errors
- ✅ `test_download_failure_no_body` - Handles missing body in S3 response

#### Presigned GET URL (3 tests)
- ✅ `test_generate_presigned_get_url_success` - Validates presigned URL generation
- ✅ `test_generate_presigned_get_url_default_expiry` - Validates default 1-hour expiry
- ✅ `test_generate_presigned_get_url_failure` - Handles URL generation errors

#### Presigned PUT URL (2 tests)
- ✅ `test_generate_presigned_put_url_success` - Validates PUT URL generation
- ✅ `test_generate_presigned_put_url_failure` - Handles PUT URL errors

#### Delete Operations (3 tests)
- ✅ `test_delete_success` - Validates successful file deletion
- ✅ `test_delete_failure_boto_error` - Handles delete errors
- ✅ `test_delete_failure_client_error` - Handles different error types

**Why these tests matter**: S3 operations are critical infrastructure. These tests ensure we handle both success and failure cases correctly, preventing data loss and providing proper error messages.

---

#### 6. `test_song_model.py` (10 tests)

Tests the Song SQLModel and Pydantic schemas.

#### Song Model (4 tests)
- ✅ `test_song_creation_valid` - Validates basic model creation with all fields
- ✅ `test_song_id_generation` - Ensures UUIDs are auto-generated and unique
- ✅ `test_song_created_at_auto_set` - Validates timestamp is automatically set
- ✅ `test_song_duration_validation` - Validates duration constraint (non-negative)

#### SongCreate Schema (4 tests)
- ✅ `test_song_create_valid` - Validates schema creation with all required fields
- ✅ `test_song_create_missing_fields` - Validates required field enforcement
- ✅ `test_song_create_negative_duration` - Validates duration constraint
- ✅ `test_song_create_zero_duration` - Validates zero duration is acceptable

#### SongRead Schema (2 tests)
- ✅ `test_song_read_from_model` - Validates model-to-schema conversion
- ✅ `test_song_read_direct_creation` - Validates direct schema creation
- ✅ `test_song_read_missing_fields` - Validates required field enforcement

#### SongUploadResponse Schema (3 tests)
- ✅ `test_song_upload_response_valid` - Validates response schema creation
- ✅ `test_song_upload_response_default_status` - Validates default "uploaded" status
- ✅ `test_song_upload_response_custom_status` - Validates custom status values
- ✅ `test_song_upload_response_missing_fields` - Validates required field enforcement

**Why these tests matter**: Data models are the foundation of the application. These tests ensure data integrity, proper validation, and correct serialization/deserialization.

---

#### 7. `test_song_routes.py` (10 tests)

Tests the FastAPI routes for song management with mocked dependencies.

#### Upload Endpoint (5 tests)
- ✅ `test_upload_success` - Validates full upload flow (validation → DB → S3)
- ✅ `test_upload_missing_filename` - Validates error handling for missing filename
- ✅ `test_upload_empty_file` - Validates error handling for empty files
- ✅ `test_upload_invalid_format` - Validates integration with validation service
- ✅ `test_upload_s3_failure_rollback` - Validates database rollback on S3 failure

#### Get Song Endpoint (3 tests)
- ✅ `test_get_song_success` - Validates successful song retrieval
- ✅ `test_get_song_not_found` - Validates 404 handling for non-existent songs
- ✅ `test_get_song_wrong_user` - Validates authorization (users can't access others' songs)

#### List Songs Endpoint (2 tests)
- ✅ `test_list_songs_empty` - Validates empty list handling
- ✅ `test_list_songs_multiple` - Validates multiple songs are returned correctly
- ✅ `test_list_songs_user_isolation` - Validates users only see their own songs

**Why these tests matter**: API routes are the public interface. These tests ensure proper request handling, authentication, authorization, error responses, and data isolation between users.

---

## Test Summary

**Total Tests**: 106 unit tests
- **Phase 1 (Authentication)**: 40 tests
- **Phase 2 (Audio Upload & Storage)**: 66 tests

**Coverage Areas**:
- ✅ Password hashing and verification (bcrypt security)
- ✅ JWT token creation and verification
- ✅ User registration and authentication
- ✅ Protected route authentication
- ✅ Audio file validation (format, size, duration)
- ✅ S3 operations (upload, download, presigned URLs, delete)
- ✅ Data models and schemas
- ✅ API endpoints (upload, get, list)
- ✅ Error handling and edge cases
- ✅ Authorization and user isolation

**Test Execution**:
```bash
# Run all unit tests
cd v2/backend
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_audio_validation.py -v

# Run specific test class
pytest tests/unit/test_audio_validation.py::TestValidateAudioFileFormat -v
```

**Performance**: All tests run in < 1 second total, making them suitable for CI/CD pipelines and rapid development feedback.

---

## Test Philosophy

These unit tests complement the integration test scripts (`scripts/for-development/test-phase1.sh` and `test-phase2.sh`) which test the full end-to-end flow with real services. The unit tests provide:

1. **Fast feedback** - Catch bugs immediately during development
2. **Isolated testing** - Test logic without external dependencies
3. **Comprehensive coverage** - Test edge cases that are hard to test in integration
4. **Documentation** - Tests serve as executable documentation of expected behavior
5. **Security validation** - Critical authentication and authorization logic is thoroughly tested

Together, unit tests and integration tests provide confidence that Phase 1 and Phase 2 functionality works correctly in both isolation and in the full system context.

