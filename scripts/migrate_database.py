#!/usr/bin/env python3
"""
Database migration script for the attendance system
"""

import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from migrations.migration_manager import migration_manager
from config.configuration_manager import config_manager


def main():
    """Run database migration"""
    logger.info("Starting database migration process...")
    logger.info("=" * 50)
    
    try:
        # Get current migration status
        logger.info("Checking migration status...")
        status = migration_manager.get_migration_status()
        
        logger.info(f"Database exists: {status.get('database_exists', False)}")
        logger.info(f"Migration needed: {status.get('migration_needed', 'unknown')}")
        
        if status.get('legacy_data', {}).get('legacy_records', 0) > 0:
            logger.info(f"Legacy records found: {status['legacy_data']['legacy_records']}")
        
        # Perform migration based on status
        migration_type = status.get('migration_needed', 'none')
        
        if migration_type == 'none':
            logger.info("No migration needed - database is up to date")
            return True
        
        elif migration_type in ['create_new', 'migrate_legacy']:
            logger.info(f"Performing migration: {migration_type}")
            
            if migration_manager.migrate_to_new_schema():
                logger.info("Migration completed successfully!")
                
                # Verify migration
                logger.info("Verifying migration...")
                verification = migration_manager.verify_migration()
                
                if verification.get('database_healthy', False):
                    logger.info("✓ Database is healthy")
                else:
                    logger.warning("⚠ Database health check failed")
                
                if verification.get('tables_accessible', False):
                    logger.info("✓ New tables are accessible")
                    logger.info(f"  - Students: {verification.get('students_count', 0)}")
                    logger.info(f"  - Classes: {verification.get('classes_count', 0)}")
                    logger.info(f"  - Records: {verification.get('records_count', 0)}")
                else:
                    logger.error("✗ New tables are not accessible")
                    if 'table_error' in verification:
                        logger.error(f"Error: {verification['table_error']}")
                
                return True
            else:
                logger.error("Migration failed!")
                return False
        
        else:
            logger.error(f"Unknown migration type: {migration_type}")
            return False
    
    except Exception as e:
        logger.error(f"Migration process failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    
    if success:
        logger.info("\n" + "=" * 50)
        logger.info("🎉 DATABASE MIGRATION COMPLETED SUCCESSFULLY!")
        logger.info("=" * 50)
        logger.info("Your database is now ready to use with the modernized system.")
        logger.info(f"Database location: {config_manager.get_database_url()}")
        
        # Show backup location if any
        backup_dir = Path("backups")
        if backup_dir.exists():
            backups = list(backup_dir.glob("*.db"))
            if backups:
                latest_backup = max(backups, key=lambda x: x.stat().st_mtime)
                logger.info(f"Latest backup: {latest_backup}")
    else:
        logger.error("\n" + "=" * 50)
        logger.error("❌ DATABASE MIGRATION FAILED!")
        logger.error("=" * 50)
        logger.error("Please check the error messages above and try again.")
        sys.exit(1)