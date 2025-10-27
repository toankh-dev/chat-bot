# Improving RAG Accuracy for Counting & Structured Queries

## 🎯 The Problem

**Your Query:**
```
"Can you count 画面ID rows in the 画面一覧 sheet?"
```

**Current Response:**
```
"Unfortunately, I couldn't find the exact count..."
```

**Why This Happens:**

### Current Embedding Strategy:
- Each **row** in Excel = 1 document in ChromaDB
- When you ask "how many rows?", the LLM only sees the top 5 most relevant rows
- The LLM can't count what it doesn't see

### Example:
```
画面一覧 sheet has 105 rows

Embedded as:
- doc_1: "Column1: value1 | Column2: value2..."
- doc_2: "Column1: value3 | Column2: value4..."
- ...
- doc_105: "Column1: value99 | Column2: value100..."

When you ask "how many rows?":
- Vector search returns only 5 most relevant documents
- LLM sees 5 rows, not 105
- LLM can't count 105 from seeing only 5
```

---

## ✅ Solution 1: Add Summary Documents (Recommended)

### What It Does:
Creates **one summary document per sheet** containing:
- Total row count
- Column names and stats
- Sample data
- Overview information

### How To Use:

**Step 1: Wait for current embedding to finish**
```bash
# Monitor until it reaches 3606/3606
powershell -ExecutionPolicy Bypass -File scripts/monitor_embedding.ps1
```

**Step 2: Add summary documents**
```bash
python scripts/add_summary_documents.py
```

This will:
- Analyze all 107 sheets
- Create 107 summary documents
- Embed them with VoyageAI
- Add to ChromaDB

**Time**: ~2 minutes (1 API call for all summaries)

### What You'll Get:

**Summary Document Example:**
```
Sheet Summary: 画面一覧

Total Rows: 109
Non-empty Rows: 105
Total Columns: 9

Columns:
- 画面ID: 105 non-null values, 90 unique
- 画面名: 102 non-null values, 88 unique
- Category: 95 non-null values, 12 unique
...

Sample Data (first 3 rows):
[Shows actual first 3 rows]

This sheet contains 105 data rows with 9 columns.
```

### Queries That Will Now Work:

✅ **Counting:**
```json
{"message": "How many rows in 画面一覧 sheet?"}
```
Response: "The 画面一覧 sheet contains 105 data rows (109 total including headers)."

✅ **Column Information:**
```json
{"message": "What columns are in the HOME sheet?"}
```
Response: "The HOME sheet has 17 columns including [list of columns]..."

✅ **Overview:**
```json
{"message": "Summarize the PRD101 sheet"}
```
Response: "The PRD101 sheet contains 71 rows with 17 columns. The main columns are..."

---

## ✅ Solution 2: Better Chunking Strategy (Advanced)

Instead of 1 document per row, use:
- **1 summary document per sheet** (metadata, counts, structure)
- **Grouped documents** (every 10-20 rows together)
- **Column-specific documents** (all values of important columns)

### Implementation:

Would require reprocessing all 3,606 documents. Not recommended right now since embedding is in progress.

---

## ✅ Solution 3: Add Query Tool to LLM (Future Enhancement)

Give the LLM a tool to directly query the Excel data:

```python
@tool
def query_excel_sheet(sheet_name: str, query_type: str):
    """
    Query Excel data directly

    Args:
        sheet_name: Name of the sheet
        query_type: "count_rows", "get_columns", "get_unique_values"
    """
    # Direct Excel access
    pass
```

This would allow:
```json
{"message": "Count rows in 画面一覧"}
```

LLM thinks: "I need to count rows → use query_excel_sheet tool"

---

## 🚀 Recommended Action Plan

### **Step 1: Let Current Embedding Finish** (in progress - 33% done)

Wait for the monitor to show:
```
Documents: 3606 / 3606 (100%)
✅ All documents embedded!
```

### **Step 2: Add Summary Documents** (~2 min)

```bash
python scripts/add_summary_documents.py
```

This adds 107 summary documents (one per sheet) to your 3,606 row documents.

Total documents: **3,713** (3,606 rows + 107 summaries)

### **Step 3: Test Counting Query**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How many rows are in the 画面一覧 sheet?",
    "conversation_id": "test-2"
  }'
```

**Expected Response:**
```
"The 画面一覧 sheet contains 105 non-empty data rows out of 109 total rows,
with 9 columns including 画面ID, 画面名, and Category."
```

---

## 📊 Current vs. Improved

### **Current System (1200/3606 documents embedded):**
- ❌ Can't count rows
- ❌ Can't list all columns
- ✅ Can find specific content
- ✅ Can answer questions about individual rows

### **After Adding Summaries:**
- ✅ Can count rows
- ✅ Can list all columns
- ✅ Can provide sheet overviews
- ✅ Can find specific content
- ✅ Can answer questions about individual rows
- ✅ Better context for the LLM

---

## 🔧 How Summary Documents Help

### Query: "How many rows in 画面一覧?"

**Without Summary:**
1. Vector search finds 5 relevant rows from 画面一覧
2. LLM sees: 5 rows
3. LLM thinks: "I only see 5 rows, can't count all"
4. Response: "I don't have the full count"

**With Summary:**
1. Vector search finds the **summary document** for 画面一覧
2. LLM sees: "Total Rows: 109, Non-empty Rows: 105"
3. LLM thinks: "The summary says 105 rows"
4. Response: "The sheet has 105 rows"

---

## 💡 Additional Improvements

### **For Better Accuracy:**

1. **Adjust Search Results Count**
   - Currently returns top 5 documents
   - Increase to 10-15 for better context
   - Edit `app/vector_store/chromadb_client.py`, line 182: `n_results=15`

2. **Add Sheet Context to Every Document**
   - Include sheet summary in each row document
   - Format: "This is row X of Y in sheet Z (which has N total rows)"

3. **Create Aggregate Documents**
   - "All 画面ID values: [list]"
   - "All Categories: [list with counts]"
   - Enable "show me all unique values" queries

---

## 📝 Summary

**Problem**: RAG can't count because each row is separate

**Solution**: Add summary documents with metadata

**Steps**:
1. Wait for embedding to finish (monitoring now)
2. Run: `python scripts/add_summary_documents.py`
3. Test counting queries
4. Enjoy accurate counts! 🎉

**Time**: 2 minutes after current embedding finishes

**Cost**: 1 VoyageAI API call (all 107 summaries in one batch)
