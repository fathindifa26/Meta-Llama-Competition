"""
Database Initialization Script
=============================

This script initializes the Face Recognition Cafe database with:
- Enhanced menu items with mood-based descriptions for AI recommendations
- Sample customers with purchase history for testing
- Proper database schema setup

Run this FIRST before starting the application:
    python init_database.py

Then start the main application:
    python main.py
"""

import os
import shutil
import random
import numpy as np
import cv2
from datetime import datetime, timedelta
from src.database import FaceDatabase

def reset_with_dummy_data():
    """Reset database dengan 2 customers dummy + enhanced menu untuk LLM (tanpa names)."""
    print("🔄 Starting database reset with enhanced menu for LLM...")
    
    # 1. Hapus database lama
    db_path = "data/face_recognition.db" 
    if os.path.exists(db_path):
        os.remove(db_path)
        print("✅ Removed old database")
    
    # 2. Hapus folder data lama (kecuali saved_faces)
    folders_to_clean = ['data/faces', 'data/embeddings']
    for folder in folders_to_clean:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"✅ Removed {folder}")
    
    # 3. Create fresh database
    print("\n🔄 Creating fresh database...")
    db = FaceDatabase()
    
    # 4. ✅ Enhanced Menu Update (untuk mood-based LLM)
    print("\n📋 Enhancing menu with mood-based descriptions...")
    enhance_menu_for_mood_ai(db)
    
    # 5. Add Customer 1 - Using existing embedding and photo (NO NAMES)
    print("\n👤 Adding Customer 1 (Real Data)...")
    customer_1_id = "john_doe_001"
    
    try:
        # Load existing embedding
        embedding_path = "saved_faces/embedding_24-09-2025-20-23-58.npy"
        photo_path = "saved_faces/face_24-09-2025-20-23-58.jpg"
        
        if os.path.exists(embedding_path) and os.path.exists(photo_path):
            # Load embedding
            embedding = np.load(embedding_path)
            print(f"   📊 Loaded embedding: shape {embedding.shape}")
            
            # Load photo
            face_image = cv2.imread(photo_path)
            if face_image is not None:
                print(f"   📷 Loaded photo: {face_image.shape}")
                
                # Add to database (NO NAME)
                success = db.add_customer(customer_1_id, face_image, embedding, confidence=0.92)
                if success:
                    print(f"   ✅ {customer_1_id} added successfully")
                else:
                    print(f"   ❌ Failed to add {customer_1_id}")
            else:
                print("   ❌ Could not load photo")
        else:
            print("   ⚠️ Real data files not found, creating dummy for Customer 1")
            # Fallback: create dummy
            face_image = create_dummy_face(customer_1_id, (100, 150, 255))
            embedding = np.random.random(512).astype(np.float32) 
            success = db.add_customer(customer_1_id, face_image, embedding, confidence=0.85)
            if success:
                print(f"   ✅ {customer_1_id} (dummy) added successfully")
            
    except Exception as e:
        print(f"   ❌ Error loading real data: {e}")
        # Fallback: create dummy
        face_image = create_dummy_face(customer_1_id, (100, 150, 255))
        embedding = np.random.random(512).astype(np.float32)
        success = db.add_customer(customer_1_id, face_image, embedding, confidence=0.85)
        if success:
            print(f"   ✅ {customer_1_id} (fallback dummy) added successfully")
    
    # 6. Add Customer 2 - Dummy data (NO NAMES)
    print("\n👤 Adding Customer 2 (Dummy Data)...")
    customer_2_id = "maria_smith_002"
    
    face_image_2 = create_dummy_face(customer_2_id, (255, 150, 100))
    embedding_2 = np.random.random(512).astype(np.float32)
    
    success = db.add_customer(customer_2_id, face_image_2, embedding_2, confidence=0.88)
    if success:
        print(f"   ✅ {customer_2_id} added successfully")
    else:
        print(f"   ❌ Failed to add {customer_2_id}")
    
    # 7. Generate Purchase History
    print("\n🛒 Generating purchase history...")
    
    # Get menu items
    menu_items = db.get_menu()
    menu_ids = [item['id'] for item in menu_items]
    print(f"   📋 Available menu items: {len(menu_items)}")
    for item in menu_items:
        print(f"      {item['id']}. {item['name']} - Rp {item['price']:,}")
        # Show enhanced description
        if 'mood_tags' in item and item['mood_tags']:
            print(f"         🎭 {item['mood_tags'][:50]}...")
    
    # Generate purchases for Customer 1
    print(f"\n   📊 Generating purchases for {customer_1_id}...")
    customer_1_purchases = [
        # Recent purchases (last 7 days)
        {"menu_id": 2, "quantity": 1, "days_ago": 1},   # Cappuccino yesterday
        {"menu_id": 1, "quantity": 2, "days_ago": 3},   # Americano 3 days ago
        {"menu_id": 3, "quantity": 1, "days_ago": 5},   # Latte 5 days ago
        {"menu_id": 2, "quantity": 1, "days_ago": 7},   # Cappuccino 7 days ago
        
        # Older purchases (to build history)
        {"menu_id": 4, "quantity": 1, "days_ago": 12},  # Cold Brew
        {"menu_id": 1, "quantity": 1, "days_ago": 18},  # Americano
        {"menu_id": 2, "quantity": 2, "days_ago": 25},  # Cappuccino x2
        {"menu_id": 5, "quantity": 1, "days_ago": 30},  # Matcha Latte
    ]
    
    for purchase in customer_1_purchases:
        purchase_time = datetime.now() - timedelta(
            days=purchase["days_ago"],
            hours=random.randint(8, 18),  # Business hours
            minutes=random.randint(0, 59)
        )
        
        success = add_purchase_directly(db, customer_1_id, purchase["menu_id"], 
                                      purchase["quantity"], purchase_time)
        if success:
            menu_name = next(m['name'] for m in menu_items if m['id'] == purchase["menu_id"])
            print(f"      ✅ {menu_name} x{purchase['quantity']} ({purchase['days_ago']} days ago)")
    
    # Generate purchases for Customer 2
    print(f"\n   📊 Generating purchases for {customer_2_id}...")
    customer_2_purchases = [
        # Recent purchases
        {"menu_id": 3, "quantity": 1, "days_ago": 2},   # Latte 2 days ago
        {"menu_id": 5, "quantity": 1, "days_ago": 4},   # Matcha 4 days ago
        {"menu_id": 3, "quantity": 2, "days_ago": 8},   # Latte x2
        
        # Older purchases  
        {"menu_id": 4, "quantity": 1, "days_ago": 15},  # Cold Brew
        {"menu_id": 5, "quantity": 1, "days_ago": 22},  # Matcha Latte
        {"menu_id": 2, "quantity": 1, "days_ago": 28},  # Cappuccino
    ]
    
    for purchase in customer_2_purchases:
        purchase_time = datetime.now() - timedelta(
            days=purchase["days_ago"],
            hours=random.randint(9, 17),
            minutes=random.randint(0, 59)
        )
        
        success = add_purchase_directly(db, customer_2_id, purchase["menu_id"],
                                      purchase["quantity"], purchase_time)
        if success:
            menu_name = next(m['name'] for m in menu_items if m['id'] == purchase["menu_id"])
            print(f"      ✅ {menu_name} x{purchase['quantity']} ({purchase['days_ago']} days ago)")
    
    # 8. Show final statistics
    print("\n📈 Final Database Statistics:")
    
    # Count customers
    import sqlite3
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM customers')
    customer_count = cursor.fetchone()[0]
    print(f"   👥 Total customers: {customer_count}")
    
    cursor.execute('SELECT COUNT(*) FROM purchases')  
    purchase_count = cursor.fetchone()[0]
    print(f"   🛒 Total purchases: {purchase_count}")
    
    # Show customer details (NO NAMES)
    cursor.execute('SELECT customer_id, total_purchases, total_spent FROM customers')
    customers = cursor.fetchall()
    for customer_id, total_purchases, total_spent in customers:
        print(f"      - {customer_id}: {total_purchases} purchases, Rp {total_spent:,}")
    
    conn.close()
    
    # 9. Test recommendations
    print("\n🎯 Testing Recommendation Features:")
    
    # Test most popular
    popular = db.get_most_popular_item()
    if popular:
        print(f"   🔥 Most popular: {popular['name']} ({popular.get('total_orders', 0)} orders)")
    
    # Test last purchases
    for customer_id in [customer_1_id, customer_2_id]:
        last = db.get_last_purchase_item(customer_id)
        if last:
            print(f"   👤 {customer_id} last bought: {last['name']} x{last['last_quantity']}")
        
        # Test full recommendations
        recommendations = db.get_menu_recommendations(customer_id)
        print(f"      - Recommendations ready: {len(recommendations)} keys")
    
    # 10. ✅ Test enhanced menu data for LLM
    print("\n🎭 Enhanced Menu for LLM:")
    sample_menu = db.get_menu()
    for item in sample_menu:
        print(f"\n   {item['id']}. {item['name']} - Rp {item['price']:,}")
        print(f"      📝 {item['description']}")
        if 'mood_tags' in item and item['mood_tags']:
            print(f"      🏷️ Tags: {item['mood_tags']}")
    
    print("\n✅ Database reset completed successfully!")
    print("🚀 Ready for LLM mood-based recommendations!")

def enhance_menu_for_mood_ai(db):
    """Update menu dengan enhanced descriptions untuk mood-based LLM."""
    enhanced_menu_data = [
        {
            "id": 1,
            "description": "Bold and straightforward coffee for focused minds. Perfect when you need clarity, energy, and no-nonsense fuel for productivity.",
            "mood_tags": "focused,energetic,determined,busy,productive,tired,morning,work,clarity,bold,straightforward"
        },
        {
            "id": 2, 
            "description": "Balanced harmony of bold espresso and velvety foam. Sophisticated comfort for social moments and contemplative breaks.",
            "mood_tags": "balanced,social,comfortable,contemplative,cozy,sophisticated,warm,afternoon,meeting,elegant,harmony"
        },
        {
            "id": 3,
            "description": "Creamy embrace of smooth espresso and silky steamed milk. Gentle comfort for stressful days and emotional moments.",
            "mood_tags": "gentle,calm,nurturing,stressed,emotional,tired,comfort,smooth,soothing,overwhelmed,embrace"
        },
        {
            "id": 4,
            "description": "Cool, smooth refreshment for hot days and chill vibes. Modern energy without the intensity, perfect for casual moments.",
            "mood_tags": "chill,refreshed,hot,relaxed,modern,trendy,cool,casual,summer,smooth,refreshing,laid-back"
        },
        {
            "id": 5,
            "description": "Zen-like calm energy from premium Japanese matcha. Mindful choice for creative souls and health-conscious moments.",
            "mood_tags": "zen,healthy,mindful,creative,peaceful,unique,premium,artistic,wellness,meditation,conscious,calm"
        }
    ]
    
    # Add mood_tags column if not exists
    import sqlite3
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('ALTER TABLE menu ADD COLUMN mood_tags TEXT')
        print("   ✅ Added mood_tags column to menu")
    except:
        print("   ⚠️ mood_tags column already exists")
    
    # Update each menu item
    for item in enhanced_menu_data:
        cursor.execute('''
            UPDATE menu 
            SET description = ?, mood_tags = ?
            WHERE id = ?
        ''', (item["description"], item["mood_tags"], item["id"]))
        
        print(f"   🎭 Enhanced menu item {item['id']} with mood context")
    
    conn.commit()
    conn.close()

def create_dummy_face(customer_id, color=(255, 100, 100)):
    """Create a simple dummy face image."""
    # Create 200x200 colored image
    face_image = np.full((200, 200, 3), color, dtype=np.uint8)
    
    # Add customer ID text
    cv2.putText(face_image, customer_id[:15], (10, 100), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(face_image, "DUMMY", (70, 130),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    return face_image

def add_purchase_directly(db, customer_id, menu_id, quantity, purchase_time):
    """Add purchase directly to database with custom timestamp."""
    try:
        import sqlite3
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        # Get menu item details
        cursor.execute('SELECT name, price FROM menu WHERE id = ?', (menu_id,))
        menu_item = cursor.fetchone()
        if not menu_item:
            conn.close()
            return False
        
        menu_name, unit_price = menu_item
        total_price = unit_price * quantity
        
        # Insert purchase
        cursor.execute('''
            INSERT INTO purchases 
            (customer_id, menu_id, quantity, total_price, purchase_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (customer_id, menu_id, quantity, total_price, purchase_time.isoformat()))
        
        # Update customer stats
        cursor.execute('''
            UPDATE customers 
            SET total_purchases = total_purchases + ?,
                total_spent = total_spent + ?,
                last_seen = ?
            WHERE customer_id = ?
        ''', (quantity, total_price, purchase_time.isoformat(), customer_id))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"      ❌ Error adding purchase: {e}")
        return False

if __name__ == "__main__":
    reset_with_dummy_data()