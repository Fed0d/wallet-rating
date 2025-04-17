import streamlit as st


def is_valid_eth_address(address: str) -> bool:
    if not isinstance(address, str):
        return False
    if not address.startswith("0x"):
        return False
    if len(address) != 42:
        return False
    hex_digits = address[2:]
    if not all(c in "0123456789abcdefABCDEF" for c in hex_digits):
        return False
    return True


st.title("Wallet Rating App!")

mode = st.selectbox(
    "Выберите режим ввода:", options=["Один кошелек", "Несколько кошельков"]
)

if mode == "Один кошелек":
    wallet_address = st.text_input("Введите адрес кошелька:")
    if wallet_address:
        if is_valid_eth_address(wallet_address):
            st.write("Введенный кошелек:", wallet_address)
        else:
            st.error("Некорректный Ethereum адрес")
else:
    uploaded_file = st.file_uploader(
        "Загрузите текстовый файл с адресами кошельков", type=["txt"]
    )
    if uploaded_file is not None:
        file_content = uploaded_file.getvalue().decode("utf-8")
        wallets = [line.strip() for line in file_content.splitlines() if line.strip()]
        valid_wallets = []
        invalid_wallets = []
        for wallet in wallets:
            if is_valid_eth_address(wallet):
                valid_wallets.append(wallet)
            else:
                invalid_wallets.append(wallet)

        if valid_wallets:
            st.write("Найденные корректные кошельки:")
            for wallet in valid_wallets:
                st.write("- ", wallet)
        if invalid_wallets:
            st.warning("Некорректные адреса:")
            for wallet in invalid_wallets:
                st.write("- ", wallet)
