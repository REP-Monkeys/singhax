# Supabase Storage Setup for Document Uploads

## Overview

The document storage system has been updated to use **Supabase Storage** (cloud storage) with automatic fallback to local filesystem storage if Supabase is not configured.

## How It Works

1. **Cloud Storage (Primary)**: If Supabase credentials are configured, files are uploaded to Supabase Storage
2. **Local Storage (Fallback)**: If Supabase is not configured or upload fails, files are saved to local filesystem

## Setup Instructions

### 1. Install Dependencies

The `supabase` package has been added to `requirements.txt`. Install it:

```bash
cd apps/backend
pip install -r requirements.txt
```

### 2. Configure Supabase Storage

1. **Create Storage Bucket**:
   - Go to your Supabase Dashboard → Storage
   - Create a new bucket named `documents`
   - Set bucket to **Private** (recommended for security) or **Public** (if you want direct URL access)

2. **Set Up Bucket Policies** (if bucket is private):
   - Go to Storage → `documents` bucket → Policies
   - Create policies that allow:
     - Service role to upload/download files
     - Authenticated users to access their own files only

   Example policy for authenticated users:
   ```sql
   -- Allow users to upload their own files
   CREATE POLICY "Users can upload own documents"
   ON storage.objects FOR INSERT
   TO authenticated
   WITH CHECK (bucket_id = 'documents' AND (storage.foldername(name))[1] = auth.uid()::text);

   -- Allow users to download their own files
   CREATE POLICY "Users can download own documents"
   ON storage.objects FOR SELECT
   TO authenticated
   USING (bucket_id = 'documents' AND (storage.foldername(name))[1] = auth.uid()::text);
   ```

### 3. Environment Variables

Ensure these are set in your `.env` file:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

The service role key is needed for server-side file operations.

### 4. Storage Structure

Files are stored in Supabase Storage with this structure:

```
documents/
  {user_id}/
    flight_confirmation/
      {uuid}.pdf
    hotel_booking/
      {uuid}.pdf
    visa_application/
      {uuid}.pdf
    itinerary/
      {uuid}.pdf
```

## Testing

1. **With Supabase Configured**:
   - Upload a document via `/api/v1/chat/upload-image`
   - Check Supabase Dashboard → Storage → `documents` bucket
   - File should appear in the bucket

2. **Without Supabase** (fallback):
   - Remove or comment out Supabase credentials
   - Upload a document
   - File should be saved to `apps/backend/uploads/documents/`

## Database Fields

The database stores:
- `file_path`: Storage path in Supabase (e.g., `documents/{user_id}/flight_confirmation/{uuid}.pdf`)
- `file_url`: Public URL (if bucket is public, otherwise None)
- `file_size`: File size in bytes
- `file_content_type`: MIME type
- `original_filename`: Original uploaded filename
- `storage_type`: "cloud" or "local" (not stored in DB, but returned in API responses)

## Download Endpoints

The download endpoint (`GET /api/v1/documents/{document_id}/file`) automatically:
- Downloads from Supabase Storage if `storage_type` is "cloud"
- Falls back to local filesystem if needed
- Uses signed URLs for private buckets

## Benefits of Cloud Storage

- ✅ Scalable: No local disk space limits
- ✅ Reliable: Built on S3-compatible storage
- ✅ Secure: Private buckets with RLS policies
- ✅ Accessible: Files accessible from anywhere
- ✅ Backup: Automatically backed up by Supabase

## Troubleshooting

**Files not uploading to Supabase?**
- Check that `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set correctly
- Verify the `documents` bucket exists in Supabase
- Check bucket policies allow service role to upload
- Check server logs for error messages

**Files uploading but can't download?**
- If bucket is private, ensure policies allow service role to download
- Check that `file_path` in database matches the storage path

**Fallback to local storage?**
- This is normal if Supabase is not configured
- Files will be saved to `apps/backend/uploads/documents/`
- The system automatically detects and handles both storage types

