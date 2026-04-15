# ✦ Dictionary Application using Radix Trie

> A lightweight English–Vietnamese dictionary application with GUI, powered by an optimized **Radix Trie (Compressed Trie)** for fast and memory-efficient string lookup.

---

## 🚀 Overview

This project implements a desktop dictionary application built with **Python** and **CustomTkinter**, supporting:

- Fast word lookup
- Insert / update / delete operations
- Autocomplete (prefix search)
- Persistent storage using JSON

Unlike traditional implementations, this project leverages a **Radix Trie** to reduce tree height and improve performance.

---

## ⚙️ Features

- ✅ Insert new words or update meanings  
- 🔍 Exact word search  
- 🧠 Autocomplete using prefix matching  
- 🗑️ Delete words with automatic tree optimization  
- 💾 Save / Load dictionary (JSON)  
- 🌳 Visualize Trie structure  

---

## 🧠 Core Idea: Radix Trie

A **Radix Trie (Compressed Trie)** is an optimized version of a Trie where:

- Each edge stores a **string instead of a single character**
- Common prefixes are merged to reduce depth

### Example

```text
[root]
  └── "app"
       ├── "le"         --> apple
       └── "licat"
              └── "ion" --> application
```


### Why Radix Trie?

| Structure | Pros | Cons |
|----------|------|------|
| Trie | Simple | Deep tree, high memory |
| Radix Trie | Compressed, faster | More complex implementation |

---

## 📊 Complexity

| Operation        | Complexity |
|----------------|-----------|
| Insert         | O(k)      |
| Search         | O(k)      |
| Delete         | O(k)      |
| Prefix Search  | O(k + m)  |

- `k`: length of word  
- `m`: number of results  

---

## 🏗️ Architecture


DictionaryApp (GUI)
│
▼
RadixTrie (Core Logic)
│
▼
JSON Storage


- **RadixTrie**: handles all data operations  
- **GUI**: user interaction via CustomTkinter  
- **Storage**: persistent dictionary  

---

## 📦 Installation

### 1. Clone repository
```bash
git clone https://github.com/ndk2024/Dictionary-Application.git
cd Dictionary-Application
```
### 2. Install dependencies
```
pip install customtkinter
```
### 3. Run application
```
python tudien.py
```
📁 Project Structure
```
Dictionary-Application/
│
├── tudien.py
├── dictionary_data.json
└── README.md
```
🔮 Future Improvements
 -   🔍 Fuzzy search (edit distance / Levenshtein)
 -   📈 Frequency-based ranking
 -   🤖 AI-powered autocomplete
 -   🌐 Web version (Flask / React)
