

import json
import os
import customtkinter as ctk
from tkinter import messagebox, filedialog

# ── Giao diện tổng thể ──────────────────────────────────────────────────────
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

SAVE_FILE = "dictionary_data.json"


# ============================================================
# CẤU TRÚC DỮ LIỆU RADIX-TRIE 
# ============================================================
class RadixNode:
    __slots__ = ("prefix", "children", "is_word", "meaning")

    def __init__(self, prefix: str = ""):
        self.prefix: str = prefix
        self.children: dict[str, "RadixNode"] = {}
        self.is_word: bool = False
        self.meaning: str | None = None


class RadixTrie:
    def __init__(self):
        self.root = RadixNode("")
        self._word_count = 0

    # ── Số từ hiện có ──────────────────────────────────────
    @property
    def word_count(self) -> int:
        return self._word_count

    # ── Normalize ──────────────────────────────────────────
    @staticmethod
    def _normalize(word: str) -> str:
        return word.strip().lower()

    # ── INSERT (hỗ trợ update nghĩa) ───────────────────────
    def insert(self, word: str, meaning: str) -> bool:
        """Trả về True nếu là từ mới, False nếu chỉ update nghĩa."""
        word = self._normalize(word)
        if not word:
            return False

        node = self.root
        i = 0

        while i < len(word):
            char = word[i]

            if char not in node.children:
                # Không có node nào match → tạo lá mới
                leaf = RadixNode(word[i:])
                leaf.is_word = True
                leaf.meaning = meaning
                node.children[char] = leaf
                self._word_count += 1
                return True

            child = node.children[char]
            # Tìm độ dài prefix chung
            j = 0
            while j < len(child.prefix) and i + j < len(word) and child.prefix[j] == word[i + j]:
                j += 1

            if j == len(child.prefix):
                # Prefix của child hoàn toàn khớp → đi sâu hơn
                node = child
                i += j
            else:
                split_node = RadixNode(child.prefix[j:])
                split_node.is_word = child.is_word
                split_node.meaning = child.meaning
                split_node.children = child.children

                # child trở thành node chung (prefix ngắn hơn)
                child.prefix = child.prefix[:j]
                child.children = {split_node.prefix[0]: split_node}
                child.is_word = False
                child.meaning = None

                if i + j == len(word):
                    # Từ mới kết thúc đúng tại child vừa tách
                    child.is_word = True
                    child.meaning = meaning
                else:
                    # Tạo lá mới cho phần còn lại của từ mới
                    new_leaf = RadixNode(word[i + j:])
                    new_leaf.is_word = True
                    new_leaf.meaning = meaning
                    child.children[new_leaf.prefix[0]] = new_leaf

                self._word_count += 1
                return True

        # Đến đây: i == len(word), ta đang đứng tại node đích
        if node.is_word:
            # Từ đã tồn tại → chỉ update nghĩa
            node.meaning = meaning
            return False
        else:
            node.is_word = True
            node.meaning = meaning
            self._word_count += 1
            return True

    # ── SEARCH ─────────────────────────────────────────────
    def search(self, word: str) -> str | None:
        """Tìm chính xác, trả về nghĩa hoặc None."""
        word = self._normalize(word)
        node = self._find_node(word)
        if node and node.is_word:
            return node.meaning
        return None

    def _find_node(self, word: str) -> RadixNode | None:
        """Tìm node kết thúc của word (đã normalize)."""
        node = self.root
        i = 0
        while i < len(word):
            char = word[i]
            if char not in node.children:
                return None
            child = node.children[char]
            plen = len(child.prefix)
            if word[i: i + plen] != child.prefix:
                return None
            node = child
            i += plen
        return node

    # ── DELETE (đã fix edge cases) ──────────────────────────
    def delete(self, word: str) -> bool:
        """Xóa từ, trả về True nếu thành công."""
        word = self._normalize(word)
        if not word:
            return False

        deleted = self._delete_recursive(self.root, word, 0)
        if deleted:
            self._word_count -= 1
        return deleted

    def _delete_recursive(self, node: RadixNode, word: str, idx: int) -> bool:
        if idx == len(word):
            if not node.is_word:
                return False
            node.is_word = False
            node.meaning = None
            # Nén: nếu chỉ có 1 con và node này không phải từ, merge xuống
            self._try_merge(node)
            return True

        char = word[idx]
        if char not in node.children:
            return False

        child = node.children[char]
        plen = len(child.prefix)

        if word[idx: idx + plen] != child.prefix:
            return False

        deleted = self._delete_recursive(child, word, idx + plen)

        if deleted:
            # Nếu child không còn con nào và không phải từ → xóa child
            if not child.children and not child.is_word:
                del node.children[char]
            # Nếu child chỉ còn 1 con và không phải từ → có thể merge
            elif len(child.children) == 1 and not child.is_word:
                self._try_merge(child)

        return deleted

    def _try_merge(self, node: RadixNode):
        """Nếu node không phải từ và chỉ có 1 con → merge prefix."""
        if node.is_word or len(node.children) != 1:
            return
        only_child = next(iter(node.children.values()))
        node.prefix += only_child.prefix
        node.is_word = only_child.is_word
        node.meaning = only_child.meaning
        node.children = only_child.children

    # ── AUTOCOMPLETE / SEARCH BY PREFIX ────────────────────
    def search_by_prefix(self, prefix: str, max_results: int = 10) -> list[tuple[str, str]]:
        """
        Trả về list[(word, meaning)] có tiền tố là prefix.
        Giới hạn max_results kết quả.
        """
        prefix = self._normalize(prefix)
        results: list[tuple[str, str]] = []
        if not prefix:
            return results

        # Tìm node kết thúc của prefix
        node = self.root
        i = 0
        accumulated = ""

        while i < len(prefix):
            char = prefix[i]
            if char not in node.children:
                return results
            child = node.children[char]
            plen = len(child.prefix)

            # Kiểm tra child.prefix có match với phần còn lại của prefix không
            remaining = prefix[i:]
            if remaining.startswith(child.prefix):
                # prefix child hoàn toàn nằm trong prefix cần tìm
                accumulated += child.prefix
                node = child
                i += plen
            elif child.prefix.startswith(remaining):
                # prefix cần tìm kết thúc giữa chừng của child.prefix
                accumulated += child.prefix
                node = child
                i = len(prefix)
            else:
                return results

        # BFS/DFS thu thập tất cả từ bắt đầu từ node này
        self._collect_words(node, accumulated, results, max_results)
        return results

    def _collect_words(self, node: RadixNode, current: str,
                       results: list, max_results: int):
        if len(results) >= max_results:
            return
        if node.is_word:
            results.append((current, node.meaning))
        for child in sorted(node.children.values(), key=lambda n: n.prefix):
            if len(results) >= max_results:
                return
            self._collect_words(child, current + child.prefix, results, max_results)

    # ── LẤY TẤT CẢ TỪ (để export) ─────────────────────────
    def get_all_words(self) -> list[tuple[str, str]]:
        results: list[tuple[str, str]] = []
        self._collect_words(self.root, "", results, max_results=10_000)
        return results

    # ── HIỂN THỊ CẤY TRIE ──────────────────────────────────
    def get_trie_structure(self) -> str:
        if not self.root.children:
            return "  Cây Radix-Trie hiện đang trống."
        lines: list[str] = []
        self._traverse(self.root, 0, lines)
        return "\n".join(lines)

    def _traverse(self, node: RadixNode, level: int, lines: list[str]):
        for char in sorted(node.children.keys()):
            child = node.children[char]
            status = f"  →  [{child.meaning}]" if child.is_word else ""
            indent = "    " * level
            lines.append(f"{indent} ┣━ {child.prefix}{status}")
            self._traverse(child, level + 1, lines)

    # ── PERSISTENCE ────────────────────────────────────────
    def save_to_file(self, filepath: str) -> bool:
        try:
            data = {word: meaning for word, meaning in self.get_all_words()}
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def load_from_file(self, filepath: str) -> int:
        """Load từ file JSON, trả về số từ đã nạp."""
        if not os.path.exists(filepath):
            return 0
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data: dict = json.load(f)
            count = 0
            for word, meaning in data.items():
                if self.insert(word, meaning):
                    count += 1
            return count
        except Exception:
            return 0


# ============================================================
# 100 TỪ MẶC ĐỊNH
# ============================================================
DEFAULT_WORDS = {
    "apple": "quả táo", "ant": "con kiến", "animal": "động vật",
    "art": "nghệ thuật", "air": "không khí", "application": "ứng dụng",
    "book": "quyển sách", "boy": "cậu bé", "bird": "con chim",
    "bear": "con gấu", "bed": "cái giường", "blue": "màu xanh dương",
    "cat": "con mèo", "car": "xe hơi", "cow": "con bò",
    "city": "thành phố", "color": "màu sắc", "cloud": "đám mây",
    "dog": "con chó", "day": "ngày", "door": "cánh cửa",
    "desk": "cái bàn làm việc", "duck": "con vịt", "dream": "giấc mơ",
    "elephant": "con voi", "eye": "con mắt", "ear": "cái tai",
    "egg": "quả trứng", "earth": "trái đất", "engine": "động cơ",
    "fish": "con cá", "fire": "ngọn lửa", "food": "thức ăn",
    "foot": "bàn chân", "flower": "bông hoa", "forest": "khu rừng",
    "girl": "cô gái", "game": "trò chơi", "green": "màu xanh lá",
    "gold": "vàng", "grass": "bãi cỏ", "garden": "khu vườn",
    "house": "ngôi nhà", "horse": "con ngựa", "hand": "bàn tay",
    "hair": "mái tóc", "head": "cái đầu", "heart": "trái tim",
    "ice": "nước đá", "iron": "sắt", "island": "hòn đảo",
    "idea": "ý tưởng", "ink": "mực", "insect": "côn trùng",
    "juice": "nước ép", "jump": "nhảy", "job": "công việc",
    "joke": "trò đùa", "joy": "niềm vui", "jungle": "rừng nhiệt đới",
    "key": "chìa khóa", "king": "nhà vua", "kite": "con diều",
    "knee": "đầu gối", "knife": "con dao", "knowledge": "kiến thức",
    "lion": "sư tử", "light": "ánh sáng", "love": "tình yêu",
    "leg": "cái chân", "lake": "cái hồ", "letter": "bức thư",
    "monkey": "con khỉ", "moon": "mặt trăng", "man": "đàn ông",
    "milk": "sữa", "money": "tiền", "mountain": "ngọn núi",
    "night": "ban đêm", "nose": "cái mũi", "name": "tên",
    "nature": "thiên nhiên", "number": "con số", "notebook": "vở ghi",
    "orange": "quả cam", "ocean": "đại dương", "oil": "dầu",
    "owl": "con cú", "onion": "củ hành", "oxygen": "ô-xy",
    "pig": "con lợn", "pen": "cái bút", "paper": "tờ giấy",
    "person": "con người", "place": "địa điểm", "planet": "hành tinh",
    "queen": "nữ hoàng", "question": "câu hỏi", "quiet": "yên tĩnh",
    "quick": "nhanh nhẹn", "quality": "chất lượng",
    "rabbit": "con thỏ", "rain": "cơn mưa", "red": "màu đỏ",
    "river": "dòng sông", "room": "căn phòng", "road": "con đường",
    "sun": "mặt trời", "star": "ngôi sao", "sea": "biển",
    "snow": "tuyết", "sky": "bầu trời", "school": "trường học",
    "tree": "cái cây", "time": "thời gian", "table": "cái bàn",
    "tea": "trà", "tiger": "con hổ", "travel": "du lịch",
}


# ============================================================
# GUI – GIAO DIỆN NGƯỜI DÙNG
# ============================================================
FONT_TITLE  = ("Segoe UI", 22, "bold")
FONT_LABEL  = ("Segoe UI", 13)
FONT_INPUT  = ("Segoe UI", 14)
FONT_BTN    = ("Segoe UI", 13, "bold")
FONT_MONO   = ("Consolas", 13)
FONT_RESULT = ("Segoe UI", 14)

COLOR_ADD    = ("#2ecc71", "#27ae60")
COLOR_SEARCH = ("#3498db", "#2980b9")
COLOR_DEL    = ("#e74c3c", "#c0392b")
COLOR_SAVE   = ("#f39c12", "#e67e22")
COLOR_LOAD   = ("#9b59b6", "#8e44ad")


class DictionaryApp:
    def __init__(self, root: ctk.CTk):
        self.trie = RadixTrie()
        self.root = root
        self.root.title("Từ Điển Radix-Trie ✦ Nâng cấp hoàn chỉnh")
        self.root.geometry("860x780")
        self.root.resizable(True, True)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(6, weight=1)

        # Nạp từ mặc định
        for word, meaning in DEFAULT_WORDS.items():
            self.trie.insert(word, meaning)

        # Tự động load file nếu có
        loaded = self.trie.load_from_file(SAVE_FILE)
        self._loaded_extra = loaded

        self._build_ui()
        self._update_stat_bar()
        self.update_display()

    # ── Xây dựng UI ──────────────────────────────────────────
    def _build_ui(self):
        # Tiêu đề
        ctk.CTkLabel(self.root, text="✦ TỪ ĐIỂN RADIX-TRIE ✦",
                     font=FONT_TITLE).grid(row=0, column=0, pady=(18, 4))

        # Thanh thống kê
        self.stat_var = ctk.StringVar()
        ctk.CTkLabel(self.root, textvariable=self.stat_var,
                     font=("Segoe UI", 12), text_color="gray").grid(row=1, column=0, pady=(0, 8))

        # ── Khung nhập liệu ──────────────────────────────────
        inp = ctk.CTkFrame(self.root, corner_radius=12)
        inp.grid(row=2, column=0, padx=40, pady=4, sticky="ew")
        inp.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(inp, text="Từ tiếng Anh:", font=FONT_LABEL).grid(
            row=0, column=0, padx=16, pady=14, sticky="w")
        self.entry_word = ctk.CTkEntry(
            inp, placeholder_text="Nhập từ (vd: apple)...",
            font=FONT_INPUT, height=38)
        self.entry_word.grid(row=0, column=1, padx=16, pady=14, sticky="ew")
        self.entry_word.bind("<KeyRelease>", self._on_word_keyrelease)

        ctk.CTkLabel(inp, text="Nghĩa tiếng Việt:", font=FONT_LABEL).grid(
            row=1, column=0, padx=16, pady=(0, 14), sticky="w")
        self.entry_meaning = ctk.CTkEntry(
            inp, placeholder_text="Nhập nghĩa (chỉ dùng khi Thêm)...",
            font=FONT_INPUT, height=38)
        self.entry_meaning.grid(row=1, column=1, padx=16, pady=(0, 14), sticky="ew")

        # ── Autocomplete dropdown ─────────────────────────────
        self.ac_frame = ctk.CTkFrame(self.root, corner_radius=8, fg_color="#1e2a38")
        # (Sẽ hiện động khi gõ)
        self.ac_listbox = ctk.CTkScrollableFrame(self.ac_frame, height=160, corner_radius=8)
        self.ac_listbox.pack(fill="both", expand=True, padx=4, pady=4)
        self._ac_buttons: list[ctk.CTkButton] = []

        # ── Kết quả tìm kiếm inline ──────────────────────────
        self.result_var = ctk.StringVar(value="")
        self.result_label = ctk.CTkLabel(
            self.root, textvariable=self.result_var,
            font=FONT_RESULT, text_color="#2ecc71", wraplength=760)
        self.result_label.grid(row=4, column=0, padx=40, pady=(0, 4))

        # ── Các nút chức năng ────────────────────────────────
        btn_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        btn_frame.grid(row=3, column=0, padx=40, pady=8)

        btn_cfg = [
            ("➕  Thêm / Cập nhật", COLOR_ADD,  self.add_word),
            ("🔍  Tìm Nghĩa",       COLOR_SEARCH, self.search_word),
            ("🗑  Xóa Từ",          COLOR_DEL,  self.delete_word),
            ("💾  Lưu JSON",        COLOR_SAVE, self.save_dict),
            ("📂  Tải JSON",        COLOR_LOAD, self.load_dict),
        ]
        for text, (fg, hv), cmd in btn_cfg:
            ctk.CTkButton(btn_frame, text=text, font=FONT_BTN,
                          fg_color=fg, hover_color=hv,
                          corner_radius=8, width=138, height=40,
                          command=cmd).pack(side="left", padx=6)

        # ── Tab view: Cây Trie | Tất cả từ ──────────────────
        ctk.CTkLabel(self.root, text="Dữ liệu từ điển:", font=("Segoe UI", 15, "bold")).grid(
            row=5, column=0, padx=40, pady=(14, 2), sticky="w")

        self.tab = ctk.CTkTabview(self.root, corner_radius=10)
        self.tab.grid(row=6, column=0, padx=40, pady=(0, 16), sticky="nsew")
        self.tab.add("🌳  Cấu trúc Trie")
        self.tab.add("📋  Danh sách từ")

        self.trie_text = ctk.CTkTextbox(
            self.tab.tab("🌳  Cấu trúc Trie"),
            font=FONT_MONO, corner_radius=8)
        self.trie_text.pack(fill="both", expand=True, padx=6, pady=6)

        self.list_text = ctk.CTkTextbox(
            self.tab.tab("📋  Danh sách từ"),
            font=FONT_MONO, corner_radius=8)
        self.list_text.pack(fill="both", expand=True, padx=6, pady=6)

    # ── Autocomplete ─────────────────────────────────────────
    def _on_word_keyrelease(self, event=None):
        self.result_var.set("")  # Clear kết quả cũ
        prefix = self.entry_word.get().strip()
        if len(prefix) < 1:
            self._hide_autocomplete()
            return

        suggestions = self.trie.search_by_prefix(prefix, max_results=8)
        if suggestions:
            self._show_autocomplete(suggestions)
        else:
            self._hide_autocomplete()

    def _show_autocomplete(self, suggestions: list[tuple[str, str]]):
        # Xóa nút cũ
        for btn in self._ac_buttons:
            btn.destroy()
        self._ac_buttons.clear()

        for word, meaning in suggestions:
            btn = ctk.CTkButton(
                self.ac_listbox,
                text=f"  {word}  →  {meaning}",
                font=("Segoe UI", 13),
                anchor="w",
                fg_color="transparent",
                hover_color="#2c3e50",
                text_color="#ecf0f1",
                height=30,
                command=lambda w=word, m=meaning: self._select_suggestion(w, m)
            )
            btn.pack(fill="x", pady=1)
            self._ac_buttons.append(btn)

        # Đặt vị trí dropdown ngay dưới khung nhập
        self.ac_frame.grid(row=3, column=0, padx=(210, 40), pady=0, sticky="ew")
        self.result_label.grid(row=4, column=0, padx=40, pady=(0, 4))

    def _hide_autocomplete(self):
        for btn in self._ac_buttons:
            btn.destroy()
        self._ac_buttons.clear()
        self.ac_frame.grid_remove()

    def _select_suggestion(self, word: str, meaning: str):
        self.entry_word.delete(0, "end")
        self.entry_word.insert(0, word)
        self.entry_meaning.delete(0, "end")
        self.entry_meaning.insert(0, meaning)
        self._hide_autocomplete()
        self.result_var.set(f"✔  Đã chọn: '{word}'  →  {meaning}")

    # ── Validate input ────────────────────────────────────────
    @staticmethod
    def _validate_word(word: str) -> str | None:
        """Trả về thông báo lỗi nếu không hợp lệ, None nếu OK."""
        if not word:
            return "Vui lòng nhập từ tiếng Anh."
        if not all(c.isalpha() or c == '-' for c in word):
            return "Từ chỉ được chứa chữ cái (a-z) và dấu gạch ngang (-)."
        return None

    # ── Các hành động chính ──────────────────────────────────
    def add_word(self):
        word    = self.entry_word.get().strip().lower()
        meaning = self.entry_meaning.get().strip()
        err = self._validate_word(word)
        if err:
            self._set_result(f"⚠  {err}", "orange")
            return
        if not meaning:
            self._set_result("⚠  Vui lòng nhập nghĩa tiếng Việt.", "orange")
            return

        is_new = self.trie.insert(word, meaning)
        self._clear_inputs()
        self._hide_autocomplete()
        if is_new:
            self._set_result(f"✔  Đã thêm từ mới: '{word}'  →  {meaning}", "#2ecc71")
        else:
            self._set_result(f"✏  Đã cập nhật nghĩa: '{word}'  →  {meaning}", "#3498db")
        self._update_stat_bar()
        self.update_display()

    def search_word(self):
        word = self.entry_word.get().strip().lower()
        err = self._validate_word(word)
        if err:
            self._set_result(f"⚠  {err}", "orange")
            return
        self._hide_autocomplete()
        meaning = self.trie.search(word)
        if meaning:
            self._set_result(f"🔍  '{word}'  →  {meaning}", "#3498db")
        else:
            # Gợi ý từ gần nhất theo prefix
            suggestions = self.trie.search_by_prefix(word[:max(1, len(word)-1)], max_results=3)
            hint = "  |  Gợi ý: " + ", ".join(w for w, _ in suggestions) if suggestions else ""
            self._set_result(f"✘  Không tìm thấy '{word}'.{hint}", "#e74c3c")

    def delete_word(self):
        word = self.entry_word.get().strip().lower()
        err = self._validate_word(word)
        if err:
            self._set_result(f"⚠  {err}", "orange")
            return
        self._hide_autocomplete()

        if self.trie.search(word) is None:
            self._set_result(f"✘  Từ '{word}' không tồn tại trong từ điển.", "#e74c3c")
            return

        self.trie.delete(word)
        self.entry_word.delete(0, "end")
        self._set_result(f"🗑  Đã xóa từ '{word}' khỏi từ điển.", "#e67e22")
        self._update_stat_bar()
        self.update_display()

    def save_dict(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="dictionary_data.json",
            title="Lưu từ điển"
        )
        if not filepath:
            return
        ok = self.trie.save_to_file(filepath)
        if ok:
            self._set_result(f"💾  Đã lưu {self.trie.word_count} từ vào '{os.path.basename(filepath)}'.", "#f39c12")
        else:
            self._set_result("✘  Lỗi khi lưu file!", "#e74c3c")

    def load_dict(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Tải từ điển"
        )
        if not filepath:
            return
        count = self.trie.load_from_file(filepath)
        self._set_result(f"📂  Đã nạp thêm {count} từ mới từ '{os.path.basename(filepath)}'.", "#9b59b6")
        self._update_stat_bar()
        self.update_display()

    # ── Cập nhật màn hình ─────────────────────────────────────
    def update_display(self):
        # Tab cây Trie
        self.trie_text.configure(state="normal")
        self.trie_text.delete("0.0", "end")
        self.trie_text.insert("0.0", self.trie.get_trie_structure())
        self.trie_text.configure(state="disabled")

        # Tab danh sách
        self.list_text.configure(state="normal")
        self.list_text.delete("0.0", "end")
        all_words = self.trie.get_all_words()
        lines = [f"  {i+1:>4}.  {w:<20} →  {m}" for i, (w, m) in enumerate(all_words)]
        self.list_text.insert("0.0", "\n".join(lines) if lines else "  Từ điển đang trống.")
        self.list_text.configure(state="disabled")

    def _update_stat_bar(self):
        self.stat_var.set(f"Tổng số từ trong từ điển: {self.trie.word_count}")

    def _set_result(self, text: str, color: str = "white"):
        self.result_label.configure(text_color=color)
        self.result_var.set(text)

    def _clear_inputs(self):
        self.entry_word.delete(0, "end")
        self.entry_meaning.delete(0, "end")


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    app = ctk.CTk()
    DictionaryApp(app)
    app.mainloop()