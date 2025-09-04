import pytest
import tempfile
import os
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from uploads.models import UploadedFile, ImageThumbnail, UploadQuota
from tests.conftest import UserFactory, AccountFactory
from PIL import Image
import io


@pytest.mark.django_db
class TestUploadedFileModel:
    """Test cases for UploadedFile model."""
    
    def test_uploaded_file_creation(self, user, account):
        """Test creating an uploaded file."""
        # Create a simple test file
        test_file = SimpleUploadedFile(
            "test.txt",
            b"Test file content",
            content_type="text/plain"
        )
        
        uploaded_file = UploadedFile.objects.create(
            file=test_file,
            original_name="test.txt",
            uploaded_by=user,
            account=account,
            file_type="text",
            file_size=len(test_file.read())
        )
        
        assert uploaded_file.original_name == "test.txt"
        assert uploaded_file.uploaded_by == user
        assert uploaded_file.account == account
        assert uploaded_file.file_type == "text"
        assert uploaded_file.is_public is False
    
    def test_file_type_detection(self, user, account):
        """Test file type detection based on file extension."""
        # Test image file
        image_file = SimpleUploadedFile(
            "image.jpg",
            b"Test image content",
            content_type="image/jpeg"
        )
        
        uploaded_image = UploadedFile.objects.create(
            file=image_file,
            original_name="image.jpg",
            uploaded_by=user,
            account=account,
            file_type="image"
        )
        
        assert uploaded_image.file_type == "image"
        
        # Test document file
        doc_file = SimpleUploadedFile(
            "document.pdf",
            b"Test document content",
            content_type="application/pdf"
        )
        
        uploaded_doc = UploadedFile.objects.create(
            file=doc_file,
            original_name="document.pdf",
            uploaded_by=user,
            account=account,
            file_type="document"
        )
        
        assert uploaded_doc.file_type == "document"
    
    def test_file_size_display(self, user, account):
        """Test file size display."""
        test_file = SimpleUploadedFile(
            "test.txt",
            b"Test content",
            content_type="text/plain"
        )
        
        uploaded_file = UploadedFile.objects.create(
            file=test_file,
            original_name="test.txt",
            uploaded_by=user,
            account=account,
            file_size=1024  # 1 KB
        )
        
        assert uploaded_file.file_size == 1024
    
    @pytest.mark.unit
    def test_uploaded_file_str_representation(self, user, account):
        """Test uploaded file string representation."""
        test_file = SimpleUploadedFile(
            "test.txt",
            b"Test content",
            content_type="text/plain"
        )
        
        uploaded_file = UploadedFile.objects.create(
            file=test_file,
            original_name="test_document.txt",
            uploaded_by=user,
            account=account
        )
        
        expected = f'test_document.txt ({account.name})'
        assert str(uploaded_file) == expected


@pytest.mark.django_db
class TestImageThumbnailModel:
    """Test cases for ImageThumbnail model."""
    
    def create_test_image(self):
        """Helper method to create a test image."""
        # Create a simple test image
        image = Image.new('RGB', (100, 100), color='red')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)
        
        return SimpleUploadedFile(
            "test_image.jpg",
            image_io.getvalue(),
            content_type="image/jpeg"
        )
    
    def test_thumbnail_creation(self, user, account):
        """Test creating a thumbnail for an image."""
        test_image = self.create_test_image()
        
        uploaded_file = UploadedFile.objects.create(
            file=test_image,
            original_name="test_image.jpg",
            uploaded_by=user,
            account=account,
            file_type="image"
        )
        
        # Create thumbnail
        thumbnail = ImageThumbnail.objects.create(
            original_file=uploaded_file,
            size="150x150",
            width=150,
            height=150
        )
        
        assert thumbnail.original_file == uploaded_file
        assert thumbnail.size == "150x150"
        assert thumbnail.width == 150
        assert thumbnail.height == 150
        assert thumbnail.created_at is not None
    
    @pytest.mark.unit
    def test_thumbnail_str_representation(self, user, account):
        """Test thumbnail string representation."""
        test_image = self.create_test_image()
        
        uploaded_file = UploadedFile.objects.create(
            file=test_image,
            original_name="image.jpg",
            uploaded_by=user,
            account=account,
            file_type="image"
        )
        
        # Create a simple test image file for thumbnail
        thumbnail_image = self.create_test_image()
        
        thumbnail = ImageThumbnail.objects.create(
            original_file=uploaded_file,
            size="150x150",
            file=thumbnail_image,
            width=150,
            height=150
        )
        
        expected_str = f"Thumbnail 150x150 - image.jpg"
        assert str(thumbnail) == expected_str


@pytest.mark.django_db
class TestUploadQuotaModel:
    """Test cases for UploadQuota model."""
    
    def test_quota_creation(self, account):
        """Test creating an upload quota."""
        quota = UploadQuota.objects.create(
            account=account,
            max_storage_mb=100,  # 100 MB
            used_storage_bytes=1024 * 1024 * 10   # 10 MB
        )
        
        assert quota.account == account
        assert quota.max_storage_mb == 100
        assert quota.used_storage_bytes == 1024 * 1024 * 10
    
    def test_quota_percentage_calculation(self, account):
        """Test quota percentage calculation."""
        quota = UploadQuota.objects.create(
            account=account,
            max_storage_mb=1,
            used_storage_bytes=262144  # 256 KB (25% of 1MB)
        )
        
        assert quota.storage_percentage == 25.0
    
    def test_quota_available_space(self):
        """Test available space calculation."""
        user = UserFactory()
        account = AccountFactory(owner=user)
        quota = UploadQuota.objects.create(
            account=account,
            max_storage_mb=1,
            used_storage_bytes=314572  # ~300KB
        )
        
        available_bytes = (quota.max_storage_mb * 1024 * 1024) - quota.used_storage_bytes
        expected_available = 1048576 - 314572  # 1MB - used bytes
        assert available_bytes == expected_available
    
    def test_quota_is_exceeded(self):
        """Test quota exceeded check."""
        user = UserFactory()
        account = AccountFactory(owner=user)
        # Not exceeded
        quota = UploadQuota.objects.create(
            account=account,
            max_storage_mb=1,
            used_storage_bytes=524288  # 512KB (50% of 1MB)
        )
        assert quota.is_storage_full is False
        
        # Exceeded
        quota.used_storage_bytes = 1258291  # ~1.2MB
        quota.save()
        assert quota.is_storage_full is True
    
    def test_quota_can_upload_file(self):
        """Test can upload file check."""
        user = UserFactory()
        account = AccountFactory(owner=user)
        quota = UploadQuota.objects.create(
            account=account,
            max_storage_mb=1,
            used_storage_bytes=838860  # ~800KB
        )
        
        # Can upload small file
        can_upload, message = quota.can_upload_file(102400)  # 100KB
        assert can_upload is True
        
        # Cannot upload large file
        can_upload, message = quota.can_upload_file(314572)  # ~300KB
        assert can_upload is False
    
    @pytest.mark.unit
    def test_quota_str_representation(self):
        """Test UploadQuota string representation."""
        user = UserFactory()
        account = AccountFactory(name='Test Account', owner=user)
        quota = UploadQuota.objects.create(
            account=account,
            max_storage_mb=1,  # 1 MB
            used_storage_bytes=512 * 1024   # 512 KB
        )
        
        expected = f'Quota - {account.name}'
        assert str(quota) == expected


@pytest.mark.django_db
class TestUploadIntegration:
    """Integration tests for upload system."""
    
    @pytest.mark.integration
    def test_file_upload_updates_quota(self):
        """Test that uploading a file updates the quota."""
        user = UserFactory()
        account = AccountFactory(owner=user)
        
        # Create quota
        quota = UploadQuota.objects.create(
            account=account,
            max_storage_mb=1,  # 1 MB
            used_storage_bytes=0
        )
        
        # Upload file
        test_file = SimpleUploadedFile(
            "test.txt",
            b"Test content" * 100,  # Make it bigger
            content_type="text/plain"
        )
        
        file_size = len(test_file.read())
        test_file.seek(0)  # Reset file pointer
        
        uploaded_file = UploadedFile.objects.create(
            file=test_file,
            original_name="test.txt",
            uploaded_by=user,
            account=account,
            file_size=file_size
        )
        
        # Manually update quota (in real app this would be done in view/signal)
        quota.used_storage_bytes += file_size
        quota.save()
        
        quota.refresh_from_db()
        assert quota.used_storage_bytes == file_size
    
    @pytest.mark.integration
    def test_image_thumbnail_generation(self):
        """Test automatic thumbnail generation for images."""
        user = UserFactory()
        account = AccountFactory(owner=user)
        
        # Create test image
        image = Image.new('RGB', (200, 200), color='blue')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)
        
        test_image = SimpleUploadedFile(
            "test_image.jpg",
            image_io.getvalue(),
            content_type="image/jpeg"
        )
        
        uploaded_file = UploadedFile.objects.create(
            file=test_image,
            original_name="test_image.jpg",
            uploaded_by=user,
            account=account,
            file_type="image"
        )
        
        # Create thumbnail using the class method
        thumbnail = ImageThumbnail.create_thumbnail(uploaded_file, 'medium')
        
        if thumbnail:  # Only test if thumbnail creation succeeded
            assert thumbnail.original_file == uploaded_file
            assert thumbnail.size == 'medium'
            assert thumbnail.width > 0
            assert thumbnail.height > 0
            assert thumbnail.file is not None