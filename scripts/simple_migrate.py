#!/usr/bin/env python3
"""
Simple database migration script for the attendance system
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

from services.simple_database_manager import simple_db_manager
from config.configuration_manager import config_manager


def main():
    """Run simple database migration"""
    logger.info("Starting simple database migration process...")
    logger.info("=" * 50)
    
    try:
        # Get current migration status
        logger.info("Checking migration status...")
        status = simple_db_manager.get_migration_status()
        
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
            
            if simple_db_manager.migrate_to_new_schema():
                logger.info("Migration completed successfully!")
                
                # Verify migration
                logger.info("Verifying migration...")
                verification = simple_db_manager.verify_migration()
                
                if verification.get('database_healthy', False):
                    logger.info("✓ Database is healthy")
                else:
                    logger.warning("⚠ Database health check failed")
                
                if verification.get('tables_accessible', False):
                    logger.info("✓ New tables are accessible")
                    logger.info(f"  - Students: {verification.get('students_count', 0)}")
                    logger.info(f"  - Classes: {verification.get('classes_count', 0)}")
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
    else:
        logger.error("\n" + "=" * 50)
        logger.error("❌ DATABASE MIGRATION FAILED!")
        logger.error("=" * 50)
        logger.error("Please check the error messages above and try again.")
        sys.exit(1)