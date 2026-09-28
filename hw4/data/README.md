# Data pack goes here

This folder is intentionally empty in the repository. Place the course data pack here so it looks like:

```
data/
├── campus_customs.db      # SQLite database (catalogue, inventory, users, chat_messages)
└── products/              # 102 product photos, e.g. basic-hoodie-big-yale.jpg
```

The backend creates `sessions`, a `page_results_json` column, and (optionally, via `backend/prepare_images.py`) `products_display/` itself.
