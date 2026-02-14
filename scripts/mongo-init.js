// MongoDB Initialization Script (Production)
// Creates application user with restricted permissions

db = db.getSiblingDB('VeillePlus');

db.createUser({
    user: 'veille_app',
    pwd: 'AppP@ss2026',
    roles: [
        { role: 'readWrite', db: 'VeillePlus' }
    ]
});

// Create indexes for performance
db.enriched_documents.createIndex({ "created_at": -1 });
db.enriched_documents.createIndex({ "source_id": 1 });
db.enriched_documents.createIndex({ "topics": 1 });
db.enriched_documents.createIndex({ "url": 1 }, { unique: true, sparse: true });

db.sources.createIndex({ "name": 1 }, { unique: true });
db.sources.createIndex({ "category": 1 });

db.users.createIndex({ "username": 1 }, { unique: true });
db.users.createIndex({ "email": 1 }, { unique: true });

db.alerts.createIndex({ "user_id": 1, "created_at": -1 });
db.alerts.createIndex({ "priority": 1 });

db.audit_logs.createIndex({ "timestamp": -1 });
db.audit_logs.createIndex({ "user_id": 1 });
db.audit_logs.createIndex({ "category": 1, "action": 1 });

print('✅ VeillePlus database initialized with indexes and app user.');
