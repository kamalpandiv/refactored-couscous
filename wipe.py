from app.components.vector_dbs.pinecone_db import PineconeDB

# Initialize the DB connection
db = PineconeDB()

# Delete the index
print(f"DELETING index: {db.index_name}...")
db.pc.delete_index(db.index_name)
print("Index deleted. Please wait 60 seconds before restarting your server.")
