from app.databases.mongo_db import MongoDBDatabase

code_extensions = {
  "general_programming_languages": [
    ".c", ".cpp", ".cc", ".cxx", ".cs", ".java", ".py", ".rb", ".js", ".ts", ".php", ".swift", ".go", ".rs", ".kt", ".kts"
  ],
  "markup_and_style": [
    ".html", ".htm", ".xml", ".css", ".scss"
  ],
  "scripting_and_shell": [
    ".sh", ".bash", ".bat", ".ps1", ".pl", ".awk"
  ],
  "data_and_configuration": [
    ".json", ".yaml", ".yml", ".toml", ".ini", ".env"
  ],
  "sql_and_database": [
    ".sql"
  ],
  "functional_and_logic_programming": [
    ".hs", ".clj", ".cljs", ".cljc", ".lisp", ".cl", ".erl", ".ml", ".rkt"
  ],
  "assembly_and_machine_code": [
    ".asm", ".s"
  ],
  "miscellaneous": [
    ".md", ".ipynb", ".r", ".m", ".v", ".sv", ".vhd", ".vhdl", ".pas", ".dart"
  ],
  "version_control": [
    ".diff", ".patch"
  ],
  "build_and_automation": [
    ".gradle", ".makefile", ".mk", ".cmake"
  ],
  "specialized_programming": [
    ".pro", ".scala"
  ]
}
mdb = MongoDBDatabase()
for key, items in code_extensions.items():
    for item in items:
        item_attr = {
            "name": item,
            "subtype": key,
            "type": "programming"
        }
        mdb.add_entry_dict(item_attr, "Extensions")
