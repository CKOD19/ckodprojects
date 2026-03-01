from flask import Flask, render_template, request, jsonify, session
from decimal import Decimal

app = Flask(__name__)
app.secret_key = "delivery_chatbot_ckod"

MENU = {
    "hamburgueres": [
        {"nome": "x-burger", "preco": Decimal("15.00")},
        {"nome": "x-salada", "preco": Decimal("18.00")},
        {"nome": "x-bacon", "preco": Decimal("22.00")},
        {"nome": "x-tudo", "preco": Decimal("25.00")},
    ],
    "pizzas": [
        {"nome": "calabresa", "preco": Decimal("35.00")},
        {"nome": "frango com catupiry", "preco": Decimal("38.00")},
        {"nome": "marguerita", "preco": Decimal("36.00")},
    ],
    "bebidas": [
        {"nome": "coca-cola 2l", "preco": Decimal("12.00")},
        {"nome": "guaraná 2l", "preco": Decimal("11.00")},
        {"nome": "suco", "preco": Decimal("7.00")},
        {"nome": "água", "preco": Decimal("4.00")},
    ]
}

# ---------------- FUNÇÕES ----------------

def format_brl(valor):
    return f"R$ {valor:.2f}".replace(".", ",")

def get_cart():
    if "cart" not in session:
        session["cart"] = {}
    return session["cart"]

def save_cart(cart):
    session["cart"] = cart
    session.modified = True

def build_numbered_menu():
    index_map = {}
    n = 1
    texto = "<b>------------ CARDÁPIO ----------</b><br><br>"

    for categoria, itens in MENU.items():

        if categoria == "hamburgueres":
            titulo = "🍔 <b>Hamburgueres</b>"
        elif categoria == "pizzas":
            titulo = "🍕 <b>Pizzas</b>"
        elif categoria == "bebidas":
            titulo = "🥤 <b>Refrigerantes</b>"

        texto += f"{titulo}:<br><br>"

        for item in itens:
            index_map[str(n)] = item
            texto += f"{n}. {item['nome'].title()} — {format_brl(item['preco'])}<br>"
            n += 1

        texto += "<br>"

    return index_map, texto

def get_index_map():
    index_map, _ = build_numbered_menu()
    return index_map

def menu_text():
    _, texto = build_numbered_menu()
    return texto

# carrinho numerado
def cart_text(cart):

    if not cart:
        return "Seu carrinho está vazio."

    total = Decimal("0.00")
    txt = "<b>SEU CARRINHO</b><br><br>"

    all_items = [i for cat in MENU.values() for i in cat]

    def get_price_by_name(name):
        for it in all_items:
            if it["nome"] == name:
                return it["preco"]
        return Decimal("0.00")

    n = 1
    for item_name, qtd in cart.items():
        preco = get_price_by_name(item_name)
        subtotal = preco * qtd
        total += subtotal
        txt += f"{n}. {item_name.title()} x{qtd} — {format_brl(subtotal)}<br>"
        n += 1

    txt += f"<br>Total: <b>{format_brl(total)}</b>"
    return txt

def set_pending(key, value):
    session[key] = value
    session.modified = True

def get_pending(key):
    return session.get(key)

def clear_pending(key):
    session.pop(key, None)
    session.modified = True

# ---------------- CHATBOT ----------------

def bot_response(msg):

    msg = msg.lower().strip()
    cart = get_cart()

    # -------- EXCLUIR --------
    if msg == "excluir":
        set_pending("pending_delete", True)
        return "Digite o NÚMERO do item que deseja excluir."

    # escolher item para excluir
    if get_pending("pending_delete"):

        if msg.isdigit():

            index_map = get_index_map()
            item = index_map.get(msg)

            if item:

                nome = item["nome"]

                if nome in cart:
                    set_pending("confirm_delete", nome)
                    clear_pending("pending_delete")

                    return (
                        f"Tem certeza que deseja excluir <b>{nome.title()}</b>?<br>"
                        "<button data-message='confirmar_excluir'>✅ Sim</button> "
                        "<button data-message='cancelar_excluir'>❌ Não</button>"
                    )

                clear_pending("pending_delete")
                return "Esse item não está no carrinho."

        return "Digite um número válido."

    # confirmação excluir
    confirm_delete = get_pending("confirm_delete")

    if confirm_delete:

        if msg == "confirmar_excluir":

            cart[confirm_delete] -= 1

            if cart[confirm_delete] <= 0:
                cart.pop(confirm_delete)

            save_cart(cart)
            clear_pending("confirm_delete")

            return [
                f"Item removido.<br><br>{cart_text(cart)}",
                "O que deseja fazer agora?<br>"
                "<button data-message='excluir'>❌ Excluir Item</button> "
                "<button data-message='cardápio'>Continuar Comprando</button> "
                "<button data-message='finalizar'>Finalizar Pedido</button>"
            ]

        if msg == "cancelar_excluir":
            clear_pending("confirm_delete")
            return "Exclusão cancelada."

    # -------- CARDÁPIO --------
    if msg in ["cardápio","cardapio","menu","c"]:

        clear_pending("pending_item")
        clear_pending("pending_quantity")

        return {
            "replies":[
                menu_text(),
                "Digite o número do item que deseja adicionar:"
            ]
        }

    pending_item = get_pending("pending_item")
    pending_qty = get_pending("pending_quantity")

    # quantidade
    if pending_item and not pending_qty:

        if msg.isdigit() and int(msg) > 0:

            qty = int(msg)
            set_pending("pending_quantity", qty)

            for cat in MENU.values():
                for it in cat:
                    if it["nome"] == pending_item:
                        preco = it["preco"]
                        return [
                            f"Adicionar {qty} x <b>{pending_item.title()}</b> "
                            f"({format_brl(preco*qty)})?<br>"
                            "<button data-message='sim'>✅ Sim</button> "
                            "<button data-message='não'>❌ Não</button>"
                        ]

        return "Digite uma quantidade válida."

    # confirmar adicionar
    if pending_item and pending_qty:

        if msg == "sim":

            qty = pending_qty
            nome = pending_item

            cart[nome] = cart.get(nome,0) + qty
            save_cart(cart)

            clear_pending("pending_item")
            clear_pending("pending_quantity")

            return [
                f"Adicionado {qty} x <b>{nome.title()}</b><br><br>{cart_text(cart)}",
                "O que deseja fazer agora?<br>"
                "<button data-message='excluir'>❌ Excluir Item</button> "
                "<button data-message='cardápio'>Continuar Comprando</button> "
                "<button data-message='finalizar'>Finalizar Pedido</button>"
            ]

        if msg == "não":

            clear_pending("pending_item")
            clear_pending("pending_quantity")
            return "Item não adicionado."

    # selecionar item
    if msg.isdigit():

        item = get_index_map().get(msg)

        if item:
            set_pending("pending_item", item["nome"])
            return "Quantidade que deseja adicionar?"

        return "Número inválido."

    # ver carrinho
    if msg in ["carrinho","ver carrinho"]:
        return cart_text(cart)

    # finalizar
    if msg == "finalizar":

        if not cart:
            return "Seu carrinho está vazio."

        texto = cart_text(cart)
        save_cart({})

        return f"Pedido finalizado!<br><br>{texto}"

    return "Não entendi."

# ---------------- ROTAS ----------------

@app.route("/")
def index():
    session.clear()
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json()
    user_message = data.get("message","")

    reply = bot_response(user_message)

    if isinstance(reply, dict):
        return jsonify(reply)

    if isinstance(reply, list):
        return jsonify({"replies":reply})

    return jsonify({"reply":reply})

if __name__ == "__main__":
    app.run(debug=True)
