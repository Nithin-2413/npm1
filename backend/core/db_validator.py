import os
import logging
from typing import Dict, Any, List, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class DBValidator:
    """
    Database validation layer for order verification
    Replicates DBResponse.DBResponse(orderID) pattern
    """
    
    def __init__(self, validation_db_url: Optional[str] = None):
        self.db_url = validation_db_url or os.getenv("DB_VALIDATION_URL")
        if not self.db_url:
            logger.warning("DB_VALIDATION_URL not configured. Database validation will be skipped.")
            self.enabled = False
        else:
            self.enabled = True
    
    def validate_order(
        self,
        order_id: str,
        expected_customer: Optional[str] = None,
        expected_location: Optional[str] = None,
        expected_status: str = "Pending"
    ) -> Dict[str, Any]:
        """
        Validate order in database
        
        Returns:
        {
            "validation_passed": bool,
            "db_order_status": str,
            "db_customer": str,
            "db_location": str,
            "discrepancies": [...]
        }
        """
        
        if not self.enabled:
            return {
                "validation_passed": False,
                "error": "Database validation not configured",
                "db_order_status": None,
                "discrepancies": ["DB_VALIDATION_URL not set"]
            }
        
        try:
            # Connect to validation database
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Query order
            query = """
                SELECT 
                    order_id,
                    status,
                    customer_name,
                    service_location,
                    quantity,
                    order_type,
                    created_at,
                    updated_at
                FROM orders
                WHERE order_id = %s
            """
            
            cursor.execute(query, (order_id,))
            order = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if not order:
                return {
                    "validation_passed": False,
                    "error": f"Order {order_id} not found in database",
                    "db_order_status": None,
                    "discrepancies": [f"Order {order_id} does not exist"]
                }
            
            # Check for discrepancies
            discrepancies = []
            
            if expected_status and order['status'] != expected_status:
                discrepancies.append(
                    f"Status mismatch: expected '{expected_status}', got '{order['status']}'"
                )
            
            if expected_customer and order['customer_name'] != expected_customer:
                discrepancies.append(
                    f"Customer mismatch: expected '{expected_customer}', got '{order['customer_name']}'"
                )
            
            if expected_location and order['service_location'] != expected_location:
                discrepancies.append(
                    f"Location mismatch: expected '{expected_location}', got '{order['service_location']}'"
                )
            
            validation_passed = len(discrepancies) == 0
            
            logger.info(
                f"Order {order_id} validation: "
                f"{'PASSED' if validation_passed else 'FAILED'} "
                f"({len(discrepancies)} discrepancies)"
            )
            
            return {
                "validation_passed": validation_passed,
                "db_order_status": order['status'],
                "db_customer": order['customer_name'],
                "db_location": order['service_location'],
                "db_quantity": order['quantity'],
                "db_order_type": order['order_type'],
                "discrepancies": discrepancies,
                "order_data": dict(order)
            }
        
        except psycopg2.Error as e:
            logger.error(f"Database validation error: {e}")
            return {
                "validation_passed": False,
                "error": f"Database error: {str(e)}",
                "db_order_status": None,
                "discrepancies": [f"Database query failed: {str(e)}"]
            }
        
        except Exception as e:
            logger.error(f"Unexpected validation error: {e}")
            return {
                "validation_passed": False,
                "error": f"Unexpected error: {str(e)}",
                "db_order_status": None,
                "discrepancies": [f"Validation failed: {str(e)}"]
            }
    
    def validate_tn_inventory(
        self,
        tn_numbers: List[str],
        expected_status: str = "Reserved"
    ) -> Dict[str, Any]:
        """
        Validate TN numbers in inventory database
        """
        
        if not self.enabled:
            return {
                "validation_passed": False,
                "error": "Database validation not configured"
            }
        
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Query TNs
            query = """
                SELECT tn_number, status, assigned_to
                FROM tn_inventory
                WHERE tn_number = ANY(%s)
            """
            
            cursor.execute(query, (tn_numbers,))
            tns = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            discrepancies = []
            found_tns = {tn['tn_number'] for tn in tns}
            
            # Check missing TNs
            for tn in tn_numbers:
                if tn not in found_tns:
                    discrepancies.append(f"TN {tn} not found in inventory")
            
            # Check status
            for tn_record in tns:
                if tn_record['status'] != expected_status:
                    discrepancies.append(
                        f"TN {tn_record['tn_number']} status: "
                        f"expected '{expected_status}', got '{tn_record['status']}'"
                    )
            
            validation_passed = len(discrepancies) == 0
            
            return {
                "validation_passed": validation_passed,
                "tns_found": len(found_tns),
                "tns_expected": len(tn_numbers),
                "discrepancies": discrepancies,
                "tn_records": [dict(tn) for tn in tns]
            }
        
        except Exception as e:
            logger.error(f"TN validation error: {e}")
            return {
                "validation_passed": False,
                "error": str(e),
                "discrepancies": [f"TN validation failed: {str(e)}"]
            }
    
    def get_order_status(self, order_id: str) -> Optional[str]:
        """Quick order status check"""
        
        if not self.enabled:
            return None
        
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            cursor.execute("SELECT status FROM orders WHERE order_id = %s", (order_id,))
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return result[0] if result else None
        
        except Exception as e:
            logger.error(f"Failed to get order status: {e}")
            return None


# Global instance
db_validator = DBValidator()
