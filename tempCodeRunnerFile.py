if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,  # INFOレベルを含む全てのログを表示
        format="[%(levelname)s] %(name)s: %(message)s",  # フォーマットの設定
    )
    root = tk.Tk()
    keyboard = KanaKeyboard(root)
    root.mainloop()
