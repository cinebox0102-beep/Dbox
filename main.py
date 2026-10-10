from datetime import date
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.camera import Camera
from app.database import InventoryDB
from app.exporter import export_csv, export_pdf

Window.clearcolor = (0.03, 0.06, 0.11, 1)

class BeepApp(App):
    bg = get_color_from_hex("#08111F")
    panel = get_color_from_hex("#111E31")
    blue = get_color_from_hex("#287BFF")
    green = get_color_from_hex("#13B981")
    red = get_color_from_hex("#F04452")
    yellow = get_color_from_hex("#F5C542")
    orange = get_color_from_hex("#F28C28")
    white = get_color_from_hex("#F4F7FB")
    muted = get_color_from_hex("#93A4B8")

    def build(self):
        self.title = "Beep Estoque Pro 2.0"
        self.db = InventoryDB()
        self.root_box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
        self.header = BoxLayout(size_hint_y=None, height=dp(64), spacing=dp(8))
        titlebox = BoxLayout(orientation="vertical")
        titlebox.add_widget(self.label("BEEP ESTOQUE PRO", 19, self.white, True, "left"))
        titlebox.add_widget(self.label("VERSÃO 2.0 • CONTROLE DE ESTOQUE", 10, self.muted, False, "left"))
        self.header.add_widget(titlebox)
        self.root_box.add_widget(self.header)
        self.body = BoxLayout(orientation="vertical")
        self.root_box.add_widget(self.body)
        self.nav = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(5))
        for caption, page in [("Início","home"),("Produtos","products"),("Scanner","scanner"),("Histórico","history")]:
            b = Button(text=caption, background_normal="", background_color=self.blue if page=="home" else self.panel)
            b.bind(on_release=lambda btn, p=page: self.show_page(p))
            self.nav.add_widget(b)
        self.root_box.add_widget(self.nav)
        self.show_page("home")
        return self.root_box

    def label(self, text, size=14, color=None, bold=False, halign="left"):
        w = Label(text=str(text), font_size=dp(size), color=color or self.white, bold=bold,
                  halign=halign, valign="middle")
        w.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        return w

    def button(self, text, callback, color=None, height=44):
        b = Button(text=text, size_hint_y=None, height=dp(height), background_normal="",
                   background_color=color or self.blue, color=self.white)
        b.bind(on_release=lambda *_: callback())
        return b

    def panel_box(self, padding=12, spacing=8):
        b = BoxLayout(orientation="vertical", padding=dp(padding), spacing=dp(spacing), size_hint_y=None)
        b.bind(minimum_height=b.setter("height"))
        from kivy.graphics import Color, RoundedRectangle
        with b.canvas.before:
            Color(*self.panel)
            b._rounded = RoundedRectangle(pos=b.pos, size=b.size, radius=[dp(14)])
        b.bind(pos=lambda inst, val: setattr(inst._rounded, "pos", val),
               size=lambda inst, val: setattr(inst._rounded, "size", val))
        return b

    def scroll(self):
        s = ScrollView(do_scroll_x=False)
        col = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10), padding=(0,0,0,dp(12)))
        col.bind(minimum_height=col.setter("height"))
        s.add_widget(col)
        return s, col

    def show_page(self, page):
        self.body.clear_widgets()
        if page == "home": self.page_home()
        elif page == "products": self.page_products()
        elif page == "scanner": self.page_scanner()
        elif page == "history": self.page_history()

    def page_home(self):
        s, col = self.scroll()
        self.body.add_widget(s)
        stats = self.db.stats()
        col.add_widget(self.label("Resumo do estoque", 22, self.white, True))
        col.add_widget(self.label("Informações atualizadas dos produtos cadastrados", 12, self.muted))
        cards = GridLayout(cols=2, spacing=dp(9), size_hint_y=None, height=dp(200))
        for title, value, color in [
            ("PRODUTOS",stats["total"],self.blue),("UNIDADES",stats["units"],self.green),
            ("VENCIDOS",stats["expired"],self.red),("VENCEM EM ATÉ 30 DIAS",stats["soon"],self.yellow),
        ]:
            card = self.panel_box(12,5)
            card.add_widget(self.label(title,10,self.muted,True))
            card.add_widget(self.label(value,29,color,True))
            cards.add_widget(card)
        col.add_widget(cards)
        low = self.panel_box()
        low.add_widget(self.label(f"ESTOQUE BAIXO: {stats['low']} produto(s)",16,self.orange,True))
        low.add_widget(self.label("Produtos com quantidade igual ou abaixo do mínimo definido.",12,self.muted))
        col.add_widget(low)
        col.add_widget(self.button("＋ Cadastrar produto", lambda: self.product_form(), self.blue))
        col.add_widget(self.button("▣ Ler ou digitar código de barras", lambda: self.show_page("scanner"), self.panel))
        col.add_widget(self.button("⇩ Exportar relatório para Excel (CSV)", lambda: self.do_export("csv"), self.green))
        col.add_widget(self.button("▤ Exportar relatório em PDF", lambda: self.do_export("pdf"), self.panel))
        alerts = self.panel_box()
        alerts.add_widget(self.label("Alertas importantes",16,self.white,True))
        urgent = [p for p in self.db.list_products("") if self.is_expired(p) or self.is_soon(p) or p["quantity"] <= p["min_stock"]]
        if not urgent:
            alerts.add_widget(self.label("Nenhum alerta no momento.",12,self.muted))
        else:
            for p in urgent[:8]:
                flags=[]
                if self.is_expired(p): flags.append("VENCIDO")
                elif self.is_soon(p): flags.append("VENCE EM BREVE")
                if p["quantity"] <= p["min_stock"]: flags.append("ESTOQUE BAIXO")
                alerts.add_widget(self.label(f"{p['name']} — {', '.join(flags)}",12,self.red if "VENCIDO" in flags else self.yellow))
        col.add_widget(alerts)

    def format_date(self, iso_date):
        if not iso_date:
            return "não informada"
        try:
            return date.fromisoformat(iso_date).strftime("%d/%m/%Y")
        except ValueError:
            return iso_date

    def parse_date_br(self, value):
        value = (value or "").strip()
        if not value:
            return None
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError:
            from datetime import datetime
            try:
                return datetime.strptime(value, "%d/%m/%Y").date().isoformat()
            except ValueError:
                raise ValueError("Informe a validade no formato DD/MM/AAAA.")

    def is_expired(self, p):
        try: return bool(p.get("expiry")) and date.fromisoformat(p["expiry"]) < date.today()
        except ValueError: return False

    def is_soon(self, p):
        try:
            d = date.fromisoformat(p["expiry"]) if p.get("expiry") else None
            return d is not None and date.today() <= d <= date.fromordinal(date.today().toordinal()+30)
        except ValueError: return False

    def page_products(self, query=""):
        self.body.clear_widgets()
        outer = BoxLayout(orientation="vertical", spacing=dp(8))
        search = TextInput(hint_text="Pesquisar por nome ou código de barras...", multiline=False, size_hint_y=None,
                           height=dp(44), background_color=self.panel, foreground_color=self.white,
                           cursor_color=self.blue, padding=dp(10))
        search.text = query
        outer.add_widget(search)
        outer.add_widget(self.button("＋ Novo produto", self.product_form, self.blue, 42))
        s, col = self.scroll()
        outer.add_widget(s)
        self.body.add_widget(outer)
        def fill(text=""):
            col.clear_widgets()
            products = self.db.list_products(text)
            if not products:
                col.add_widget(self.label("Nenhum produto encontrado.",14,self.muted))
            for p in products:
                card = self.panel_box(10,5)
                state = "VENCIDO" if self.is_expired(p) else ("VENCE EM BREVE" if self.is_soon(p) else "OK")
                card.add_widget(self.label(p["name"],16,self.white,True))
                card.add_widget(self.label(f"Código: {p.get('barcode') or '-'}  •  Qtd: {p['quantity']}  •  Mínimo: {p['min_stock']}",12,self.muted))
                card.add_widget(self.label(f"Validade: {self.format_date(p.get('expiry'))}  •  {state}",12,self.red if state=="VENCIDO" else (self.yellow if state=="VENCE EM BREVE" else self.green)))
                actions = BoxLayout(size_hint_y=None,height=dp(38),spacing=dp(5))
                for txt, cb, color in [
                    ("Entrada",lambda pid=p["id"]: self.movement_form(pid,"ENTRADA"),self.green),
                    ("Saída",lambda pid=p["id"]: self.movement_form(pid,"SAÍDA"),self.orange),
                    ("Editar",lambda prod=p: self.product_form(prod),self.blue),
                    ("Excluir",lambda pid=p["id"]: self.confirm_delete(pid),self.red),
                ]:
                    actions.add_widget(self.button(txt,cb,color,36))
                card.add_widget(actions)
                col.add_widget(card)
        search.bind(text=lambda inst, val: fill(val))
        fill(query)

    def product_form(self, product=None, preset_barcode=""):
        is_edit = product is not None
        content = BoxLayout(orientation="vertical", spacing=dp(7), padding=dp(12))
        fields = {}
        field_defs = [
            ("name","Nome do produto",product["name"] if is_edit else ""),
            ("barcode","Código de barras",product.get("barcode") or "" if is_edit else preset_barcode),
            ("description","Descrição",product.get("description") or "" if is_edit else ""),
            ("quantity","Quantidade inicial (somente novo produto)",str(product["quantity"]) if is_edit else "0"),
            ("min_stock","Quantidade mínima em estoque",str(product["min_stock"]) if is_edit else "0"),
            ("expiry","Validade (DD/MM/AAAA)",product.get("expiry") or "" if is_edit else ""),
        ]
        for key,hint,value in field_defs:
            inp = TextInput(hint_text=hint,text=value,multiline=False,size_hint_y=None,height=dp(42),
                            background_color=self.panel,foreground_color=self.white,cursor_color=self.blue)
            fields[key]=inp
            content.add_widget(inp)
        popup = Popup(title="Editar produto" if is_edit else "Cadastrar produto",content=content,
                      size_hint=(.94,.88),auto_dismiss=True)
        content.add_widget(self.button("Salvar",lambda: save(),self.green))
        def save():
            try:
                name=fields["name"].text.strip()
                if not name: raise ValueError("Informe o nome do produto.")
                qty=int(fields["quantity"].text or "0")
                minimum=int(fields["min_stock"].text or "0")
                if qty < 0 or minimum < 0: raise ValueError("Quantidade não pode ser negativa.")
                expiry=self.parse_date_br(fields["expiry"].text)
                if is_edit:
                    self.db.update_product(product["id"],name,fields["barcode"].text,fields["description"].text,minimum,expiry)
                    if qty != product["quantity"]:
                        delta=qty-product["quantity"]
                        self.db.move(product["id"],"ENTRADA" if delta>0 else "SAÍDA",abs(delta),"Ajuste pelo cadastro")
                else:
                    self.db.add_product(name,fields["barcode"].text,fields["description"].text,qty,minimum,expiry)
                popup.dismiss()
                self.show_page("products")
            except Exception as e:
                self.notice(str(e) if str(e) else "Confira os campos e tente novamente.")
        popup.open()

    def movement_form(self, pid, kind="ENTRADA"):
        p=self.db.get_product(pid)
        if not p: return
        content=BoxLayout(orientation="vertical",spacing=dp(8),padding=dp(12))
        content.add_widget(self.label(f"{p['name']}  •  saldo: {p['quantity']}",14,self.white,True))
        qty=TextInput(hint_text="Quantidade",multiline=False,input_filter="int",size_hint_y=None,height=dp(44))
        note=TextInput(hint_text="Observação (opcional)",multiline=False,size_hint_y=None,height=dp(44))
        content.add_widget(qty); content.add_widget(note)
        kind_spinner=Spinner(text=kind,values=("ENTRADA","SAÍDA"),size_hint_y=None,height=dp(42))
        content.add_widget(kind_spinner)
        popup=Popup(title="Movimentação de estoque",content=content,size_hint=(.9,.55))
        def save():
            try:
                self.db.move(pid,kind_spinner.text,int(qty.text),note.text)
                popup.dismiss(); self.show_page("products")
            except Exception as e: self.notice(str(e))
        content.add_widget(self.button("Confirmar movimentação",save,self.green))
        popup.open()

    def confirm_delete(self, pid):
        p=self.db.get_product(pid)
        if not p: return
        content=BoxLayout(orientation="vertical",spacing=dp(10),padding=dp(12))
        content.add_widget(self.label(f"Excluir '{p['name']}' e seu histórico?",14,self.white))
        pop=Popup(title="Confirmar exclusão",content=content,size_hint=(.85,.35))
        row=BoxLayout(size_hint_y=None,height=dp(42),spacing=dp(8))
        row.add_widget(self.button("Cancelar",pop.dismiss,self.panel))
        def delete():
            self.db.delete_product(pid); pop.dismiss(); self.show_page("products")
        row.add_widget(self.button("Excluir",delete,self.red))
        content.add_widget(row); pop.open()

    def page_scanner(self):
        s,col=self.scroll()
        self.body.add_widget(s)
        col.add_widget(self.label("Leitor de código de barras",22,self.white,True))
        col.add_widget(self.label("Use a câmera quando compatível ou digite o código de barras abaixo.",12,self.muted))
        code=TextInput(hint_text="Código de barras",multiline=False,size_hint_y=None,height=dp(48),
                       background_color=self.panel,foreground_color=self.white,cursor_color=self.blue)
        col.add_widget(code)
        col.add_widget(self.button("Pesquisar código de barras",lambda: self.lookup_barcode(code.text),self.blue))
        col.add_widget(self.button("Cadastrar produto com este código",lambda: self.product_form(preset_barcode=code.text.strip()),self.green))
        # Camera preview is optional; actual decoding depends on native camera/barcode dependencies.
        try:
            camera=Camera(play=False,resolution=(640,480),size_hint_y=None,height=dp(220))
            col.add_widget(camera)
            col.add_widget(self.button("Ativar câmera (prévia)",lambda: self.toggle_camera(camera),self.panel))
            col.add_widget(self.label("A prévia da câmera não significa que a leitura automática esteja habilitada nesta versão.",11,self.muted))
        except Exception:
            col.add_widget(self.label("A câmera não está disponível neste dispositivo ou ambiente.",11,self.muted))

    def toggle_camera(self, camera):
        camera.play = not camera.play
        self.notice("Câmera ativada." if camera.play else "Câmera desativada.")

    def lookup_barcode(self, barcode):
        barcode=barcode.strip()
        if not barcode:
            self.notice("Digite ou leia um código de barras.")
            return
        p=self.db.find_barcode(barcode)
        if p:
            self.show_page("products")
            self.notice(f"Produto encontrado: {p['name']} • quantidade: {p['quantity']}")
        else:
            self.product_form(preset_barcode=barcode)

    def page_history(self):
        s,col=self.scroll()
        self.body.add_widget(s)
        col.add_widget(self.label("Histórico de movimentações",21,self.white,True))
        rows=self.db.movements(150)
        if not rows: col.add_widget(self.label("Ainda não há movimentações registradas.",13,self.muted))
        for m in rows:
            card=self.panel_box(10,4)
            tint=self.green if m["kind"]=="ENTRADA" else self.orange
            card.add_widget(self.label(f"{m['kind']} • {m['name'] or 'Produto removido'}",14,tint,True))
            card.add_widget(self.label(f"Quantidade: {m['quantity']} • {m['created_at']}",11,self.muted))
            if m.get("note"): card.add_widget(self.label(m["note"],11,self.muted))
            col.add_widget(card)

    def do_export(self, kind):
        try:
            products=self.db.list_products("")
            path=export_csv(products) if kind=="csv" else export_pdf(products)
            self.notice(f"Relatório salvo em:\\n{path}")
        except Exception as e:
            self.notice(str(e))

    def notice(self, message):
        pop=Popup(title="Beep Estoque Pro",content=Label(text=str(message),color=self.white),
                  size_hint=(.88,.35),background_color=self.panel)
        pop.open()

if __name__ == "__main__":
    BeepApp().run()
