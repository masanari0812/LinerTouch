import tkinter as tk


class KanaKeyboard:
    def __init__(self, root):
        self.root = root
        self.root.title("50音キーボード")

        # 入力用エントリー
        self.entry = tk.Entry(root, width=40, font=("Arial", 20))
        self.entry.grid(row=0, column=0, columnspan=10)
        self.cursor_x = 0
        self.cursor_y = 0
        # 50音キーボード配列
        self.kana_keys = [
            ["あ", "い", "う", "え", "お"],
            ["か", "き", "く", "け", "こ"],
            ["さ", "し", "す", "せ", "そ"],
            ["た", "ち", "つ", "て", "と"],
            ["な", "に", "ぬ", "ね", "の"],
            ["は", "ひ", "ふ", "へ", "ほ"],
            ["ま", "み", "む", "め", "も"],
            ["や", "　", "ゆ", "　", "よ"],
            ["ら", "り", "る", "れ", "ろ"],
            ["わ", "　", "を", "　", "ん"],
        ]
        self.kana_keys = [list(row) for row in zip(*self.kana_keys)]
        # キーボードボタンを作成
        for i, row in enumerate(self.kana_keys):
            for j, kana in enumerate(row):
                if kana:  # 空でない場合にボタンを配置
                    button = tk.Button(
                        root,
                        text=kana,
                        width=4,
                        height=1,
                        font=("Arial", 20),
                        command=lambda k=kana: self.insert_kana(k),
                    )
                    button.grid(row=i + 1, column=j, padx=5, pady=5)

    def insert_kana(self, kana):
        # エントリーに選択した文字を挿入
        self.entry.insert(tk.END, kana)


# メインプログラム
root = tk.Tk()
app = KanaKeyboard(root)
root.mainloop()
