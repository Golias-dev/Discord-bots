import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
from discord import app_commands, ui
from discord import ui, Embed, Color, SelectOption, Interaction, ButtonStyle
import random
import json
import os
import asyncio
from datetime import datetime, timedelta




intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix='.', intents=intents)



@bot.event
async def on_ready():
    print(f'Bot online como {bot.user}')


@bot.event
async def on_command(ctx):
    try:
        await ctx.message.delete(delay=1)
    except discord.Forbidden:
        pass  # Sem permissão para deletar, ignora
    except discord.HTTPException:
        pass  # Falha ao deletar, ignora

@bot.before_invoke
async def auto_delete_bot_msgs(ctx):
    original_send = ctx.send

    async def send_with_delete(*args, **kwargs):
        kwargs["delete_after"] = kwargs.get("delete_after", 10)  # define tempo padrão
        return await original_send(*args, **kwargs)

    ctx.send = send_with_delete  # sobrescreve o ctx.send

#Painel de Comandos -----------------------------------------------------
@bot.command(name="ajuda")
async def ajuda(ctx):
    class AjudaView(discord.ui.View):
        def __init__(self, user):
            super().__init__(timeout=60)
            self.user = user
            self.paginas = [
                self.embed_premium(),
                self.embed_moderacao(),
                self.embed_utilitarios()
            ]
            self.pagina_atual = 0

        def embed_premium(self):
            embed = discord.Embed(title="🎖 Comandos Premium", color=discord.Color.gold())
            embed.add_field(name="`painelpremium`", value="Abrir painel para criar cargo e call exclusiva.", inline=False)
            embed.add_field(name="`daracesso @usuário`", value="Dar acesso ao seu cargo/call Premium para outro usuário.", inline=False)
            embed.add_field(name="`deletaracesso`", value="Deletar seu cargo e call exclusiva.", inline=False)
            embed.add_field(name="`meucargo`", value="Ver seu cargo e call exclusivos.", inline=False)
            return embed

        def embed_moderacao(self):
            embed = discord.Embed(title="🛠 Comandos de Moderação", color=discord.Color.red())
            embed.add_field(name="`limpar <quantidade>`", value="Limpa mensagens do chat.", inline=False)
            embed.add_field(name="`ban @usuário [motivo]`", value="Bane um usuário do servidor.", inline=False)
            return embed

        def embed_utilitarios(self):
            embed = discord.Embed(title="📋 Comandos Utilitários", color=discord.Color.blurple())
            embed.add_field(name="`embedpainel`", value="Criador de embeds interativo (ADM).", inline=False)
            embed.add_field(name="`/criar_embed`", value="Cria um embed personalizado via painel.", inline=False)
            return embed

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            if interaction.user != self.user:
                await interaction.response.send_message("❌ Apenas quem usou o comando pode interagir!", ephemeral=True)
                return False
            return True

        @discord.ui.button(label="◀️", style=discord.ButtonStyle.gray)
        async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.pagina_atual = (self.pagina_atual - 1) % len(self.paginas)
            await interaction.response.edit_message(embed=self.paginas[self.pagina_atual], view=self)

        @discord.ui.button(label="▶️", style=discord.ButtonStyle.gray)
        async def proximo(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.pagina_atual = (self.pagina_atual + 1) % len(self.paginas)
            await interaction.response.edit_message(embed=self.paginas[self.pagina_atual], view=self)

    view = AjudaView(ctx.author)
    await ctx.send(embed=view.paginas[0], view=view)

# Sincronizar comandos de barra
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"🌐 Comandos de barra sincronizados: {[cmd.name for cmd in synced]}")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")

#BOAS VINDAS -----------------------------------------------------
# Evento chamado quando um novo membro entra no servidor
@bot.event
async def on_member_join(member: discord.Member):
    print(f'{member} entrou no servidor.')  # Debug

    guild = member.guild
    system_channel = guild.system_channel

    if system_channel is None:
        print("Nenhum canal de boas-vindas configurado.")
        return

    embed = discord.Embed(
        title="**Bem-vindo(a)!**",
        description=(
            f"Salve {member.mention}! Você acabou de entrar no servidor do **{guild.name}**.\n"
            "Aqui você poderá se interagir com amigos, conversar e trocar umas ideias com a gente."
        ),
        color=discord.Color.dark_purple()
    )

    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name="💀 Leia as regras!", value="Leia ou ban!\n#📏┃regras", inline=True)
    embed.add_field(name="📣 Vem falar com a gente.", value="#💬┃chat-geral", inline=True)
    embed.add_field(name="🪪 ID do usuário:", value=f"{member.id}", inline=False)
    embed.set_image(url="https://media.discordapp.net/attachments/1322098001623121940/1354057716586250273/a_22d4dd4beaede09386aa04cc26303ece_1.gif?ex=67f462c4&is=67f31144&hm=17539c74aed52c0be42cb9ac867a0da00614e5e707de0d9af6c5cd1032555a51&")  # opcional

    await system_channel.send(embed=embed)



#Criar embeds profissionais -----------------------------------------------------
# Variáveis suportadas
def aplicar_variaveis(texto: str, member: discord.Member):
    return texto.replace("{user.name}", member.name)\
               .replace("{user.mention}", member.mention)\
               .replace("{user.id}", str(member.id))\
               .replace("{server.name}", member.guild.name)


class PainelCriador(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=600)
        self.author_id = author_id

    async def interaction_check(self, interaction):
        return interaction.user.id == self.author_id

    @discord.ui.button(label="📝 Título", style=discord.ButtonStyle.primary)
    async def editar_titulo(self, interaction, _):
        await interaction.response.send_modal(ModalTitulo(self.author_id))

    @discord.ui.button(label="📄 Descrição", style=discord.ButtonStyle.primary)
    async def editar_desc(self, interaction, _):
        await interaction.response.send_modal(ModalDescricao(self.author_id))

    @discord.ui.button(label="🖼️ Imagem/Thumbnail", style=discord.ButtonStyle.secondary)
    async def editar_imgs(self, interaction, _):
        await interaction.response.send_modal(ModalImagens(self.author_id))

    @discord.ui.button(label="🎨 Cor", style=discord.ButtonStyle.secondary)
    async def cor_embed(self, interaction, _):
        options = [
            discord.SelectOption(label="Roxo", value="dark_purple"),
            discord.SelectOption(label="Azul", value="blue"),
            discord.SelectOption(label="Verde", value="green"),
            discord.SelectOption(label="Vermelho", value="red")
        ]

        async def callback(i):
            cores = {
                "dark_purple": discord.Color.dark_purple(),
                "blue": discord.Color.blue(),
                "green": discord.Color.green(),
                "red": discord.Color.red()
            }
            user_embed_data[self.author_id]["color"] = cores[i.data["values"][0]]
            await i.response.send_message("🎨 Cor atualizada!", ephemeral=True)

        select = discord.ui.Select(placeholder="Escolha uma cor", options=options)
        select.callback = callback
        view = discord.ui.View()
        view.add_item(select)
        await interaction.response.send_message("🎨 Selecione uma cor:", view=view, ephemeral=True)

    @discord.ui.button(label="➕ Campo", style=discord.ButtonStyle.success)
    async def add_field(self, interaction, _):
        await interaction.response.send_modal(ModalCampo(self.author_id))

    @discord.ui.button(label="📤 Enviar", style=discord.ButtonStyle.green)
    async def enviar(self, interaction, _):
        data = user_embed_data.get(self.author_id)
        if not data:
            return await interaction.response.send_message("❌ Sem dados para embed.", ephemeral=True)

        await interaction.response.send_modal(ModalEscolherCanal(self.author_id))

    @discord.ui.button(label="🧹 Limpar", style=discord.ButtonStyle.danger)
    async def limpar(self, interaction, _):
        user_embed_data[self.author_id] = {}
        await interaction.response.send_message("🧼 Dados resetados.", ephemeral=True)


class ModalTitulo(discord.ui.Modal, title="Título"):
    def __init__(self, uid):
        self.uid = uid
        super().__init__()

    titulo = discord.ui.TextInput(label="Título do Embed", placeholder="Ex: Bem-vindo(a) {user.name}")

    async def on_submit(self, interaction):
        user_embed_data.setdefault(self.uid, {})["title"] = self.titulo.value
        await interaction.response.send_message("✅ Título atualizado.", ephemeral=True)


class ModalDescricao(discord.ui.Modal, title="Descrição"):
    def __init__(self, uid):
        self.uid = uid
        super().__init__()

    desc = discord.ui.TextInput(label="Descrição", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction):
        user_embed_data.setdefault(self.uid, {})["description"] = self.desc.value
        await interaction.response.send_message("✅ Descrição atualizada.", ephemeral=True)


class ModalImagens(discord.ui.Modal, title="Imagens"):
    def __init__(self, uid):
        self.uid = uid
        super().__init__()

    thumb = discord.ui.TextInput(label="URL da Thumbnail", required=False)
    image = discord.ui.TextInput(label="URL da Imagem principal", required=False)

    async def on_submit(self, interaction):
        data = user_embed_data.setdefault(self.uid, {})
        data["thumbnail"] = self.thumb.value
        data["image"] = self.image.value
        await interaction.response.send_message("🖼️ Imagens atualizadas.", ephemeral=True)


class ModalCampo(discord.ui.Modal, title="Adicionar Campo"):
    def __init__(self, uid):
        self.uid = uid
        super().__init__()

    nome = discord.ui.TextInput(label="Nome do campo")
    valor = discord.ui.TextInput(label="Valor do campo", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction):
        campos = user_embed_data.setdefault(self.uid, {}).setdefault("fields", [])
        campos.append({"name": self.nome.value, "value": self.valor.value})
        await interaction.response.send_message("✅ Campo adicionado.", ephemeral=True)


class ModalEscolherCanal(discord.ui.Modal, title="Escolher Canal"):
    def __init__(self, uid):
        self.uid = uid
        super().__init__()

    canal_id = discord.ui.TextInput(label="ID do canal para enviar o embed")

    async def on_submit(self, interaction):
        canal = interaction.guild.get_channel(int(self.canal_id.value))
        if not canal:
            return await interaction.response.send_message("❌ Canal não encontrado.", ephemeral=True)

        data = user_embed_data[self.uid]
        embed = discord.Embed(
            title=aplicar_variaveis(data.get("title", ""), interaction.user),
            description=aplicar_variaveis(data.get("description", ""), interaction.user),
            color=data.get("color", discord.Color.default())
        )

        if data.get("thumbnail"):
            embed.set_thumbnail(url=data["thumbnail"])
        if data.get("image"):
            embed.set_image(url=data["image"])

        for campo in data.get("fields", []):
            embed.add_field(name=aplicar_variaveis(campo["name"], interaction.user), value=aplicar_variaveis(campo["value"], interaction.user), inline=False)

        await canal.send(embed=embed)
        await interaction.response.send_message("📨 Embed enviado com sucesso!", ephemeral=True)


@bot.tree.command(name="criar_embed", description="Crie um embed personalizado com painel interativo")
async def criar_embed(interaction: discord.Interaction):
    user_embed_data[interaction.user.id] = {}
    view = PainelCriador(author_id=interaction.user.id)
    await interaction.response.send_message("🛠️ Painel de criação de Embed:", view=view, ephemeral=True)

    #Comando de Premium ------------------------------------------------------

user_roles = {}
PREMIUM_ROLE_NAME = "Premium"
PREMIUM_CATEGORY_NAME = "🔞| Premium"

# Função para converter cor
def parse_hex_color(hex_str):
    try:
        return discord.Color(int(hex_str.lstrip("#"), 16))
    except:
        return discord.Color.default()

# === Modal com 3 perguntas ===
class CustomRoleModal(discord.ui.Modal, title="Criar seu cargo e call exclusiva"):
    role_name = discord.ui.TextInput(label="Nome do Cargo", placeholder="Ex: Galera do Kaick", max_length=30)
    call_name = discord.ui.TextInput(label="Nome da Call", placeholder="Ex: Sala Privada", max_length=50)
    role_color = discord.ui.TextInput(label="Cor do Cargo (hex)", placeholder="Ex: #3498db ou #FF00FF", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        author = interaction.user

        if author.id in user_roles:
            await interaction.response.send_message("❌ Você já criou seu cargo exclusivo.", ephemeral=True)
            return

        # Criar cargo com cor personalizada
        color = parse_hex_color(self.role_color.value) if self.role_color.value else discord.Color.default()
        new_role = await guild.create_role(name=self.role_name.value, color=color)
        await author.add_roles(new_role)

        # Criar ou encontrar categoria Premium
        category = discord.utils.get(guild.categories, name=PREMIUM_CATEGORY_NAME)
        if not category:
            category = await guild.create_category(PREMIUM_CATEGORY_NAME)

        # Permissões da call
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=True, connect=False),
            new_role: discord.PermissionOverwrite(view_channel=True, connect=True, speak=True)
        }

        # Criar call privada
        voice_channel = await guild.create_voice_channel(
            name=f" {self.call_name.value}",
            overwrites=overwrites,
            category=category
        )

        user_roles[author.id] = {
            "role_id": new_role.id,
            "channel_id": voice_channel.id
        }

        await interaction.response.send_message(
            f"✅ Cargo `{new_role.name}` e call `{voice_channel.name}` criados com sucesso!",
            ephemeral=True
        )

# View com botão
class RoleCreateView(discord.ui.View):
    @discord.ui.button(label="Criar Cargo e Call", style=discord.ButtonStyle.green)
    async def create_role_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        premium_role = discord.utils.get(interaction.user.roles, name=PREMIUM_ROLE_NAME)
        if not premium_role:
            await interaction.response.send_message("❌ Apenas membros com o cargo Premium podem usar isso.", ephemeral=True)
            return
        await interaction.response.send_modal(CustomRoleModal())

# Comando para abrir painel
@bot.command(name="painelpremium")
async def painel_premium(ctx):
    embed = discord.Embed(
        title="🎖 Painel Premium",
        description="Se você tem o cargo **Premium**, pode criar um cargo exclusivo e uma call privada.\nVocê só pode criar **um**!",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed, view=RoleCreateView())

# Comando para dar o cargo a outro usuário
@bot.command(name="daracesso")
async def dar_acesso(ctx, membro: discord.Member):
    if ctx.author.id not in user_roles:
        await ctx.send("❌ Você ainda não criou seu cargo exclusivo.")
        return

    role_id = user_roles[ctx.author.id]["role_id"]
    role = ctx.guild.get_role(role_id)

    if not role:
        await ctx.send("❌ Cargo não encontrado.")
        return

    await membro.add_roles(role)
    await ctx.send(f"✅ {membro.mention} agora tem acesso ao cargo `{role.name}` e à call privada!")

# Comando para deletar o cargo e canal criados
@bot.command(name="deletaracesso")
async def deletar_acesso(ctx):
    if ctx.author.id not in user_roles:
        await ctx.send("❌ Você não criou cargo nem call.")
        return

    data = user_roles.pop(ctx.author.id)
    role = ctx.guild.get_role(data["role_id"])
    channel = ctx.guild.get_channel(data["channel_id"])

    if role:
        await role.delete()
    if channel:
        await channel.delete()

    await ctx.send("🗑️ Cargo e call foram deletados com sucesso!")

# Comando para listar o que o usuário criou
@bot.command(name="meucargo")
async def meu_cargo(ctx):
    if ctx.author.id not in user_roles:
        await ctx.send("❌ Você ainda não criou um cargo.")
        return

    data = user_roles[ctx.author.id]
    role = ctx.guild.get_role(data["role_id"])
    channel = ctx.guild.get_channel(data["channel_id"])

    embed = discord.Embed(title="📦 Seu Cargo Premium", color=discord.Color.purple())
    embed.add_field(name="Cargo:", value=role.mention if role else "❌ Deletado", inline=False)
    embed.add_field(name="Canal de Voz:", value=channel.mention if channel else "❌ Deletado", inline=False)

    await ctx.send(embed=embed)



    #comando de lipar o chat 
@bot.command(name="limpar")
@commands.has_permissions(manage_messages=True)
async def limpar(ctx, quantidade: int):
    if quantidade <= 0:
        await ctx.send("❌ Digite um número maior que zero.", delete_after=5)
        return

    try:
        await ctx.channel.purge(limit=quantidade + 1)  # +1 para incluir o comando
        msg = await ctx.send(f"✅ {quantidade} mensagens deletadas.")
        await msg.delete(delay=3)
    except discord.Forbidden:
        await ctx.send("❌ Não tenho permissão para deletar mensagens.", delete_after=5)
    except Exception as e:
        await ctx.send(f"❌ Erro: {e}", delete_after=5)

@bot.command(name="ban", help="Bane um usuário do servidor.")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, motivo="Sem motivo"):
    try:
        await member.ban(reason=motivo)
        await ctx.send(f"✅ {member.mention} foi banido!\n📄 Motivo: `{motivo}`", delete_after=10)
    except discord.Forbidden:
        await ctx.send("🚫 Não tenho permissão para banir esse usuário.", delete_after=10)
    except discord.HTTPException:
        await ctx.send("❌ Ocorreu um erro ao tentar banir o usuário.", delete_after=10)


user_embed_data = {}

class EmbedCreatorModal(ui.Modal, title="Criador de Embed"):
    titulo = ui.TextInput(label="Título do Embed", placeholder="Digite o título", max_length=256)
    descricao = ui.TextInput(label="Descrição/Mensagem", placeholder="Digite o conteúdo", style=discord.TextStyle.paragraph)
    imagem_url = ui.TextInput(label="URL da imagem/GIF", placeholder="Opcional - cole o link da imagem", required=False)
    cor_hex = ui.TextInput(label="Cor do Embed (hex)", placeholder="Ex: #ff0000", required=False)
    posicao_imagem = ui.TextInput(label="Posição da imagem (thumbnail, imagem, footer)", placeholder="imagem", required=False)

    def __init__(self, canais):
        super().__init__()
        self.canais = canais

    async def on_submit(self, interaction: Interaction):
        canal = self.canais.get(interaction.user.id)
        if not canal:
            await interaction.response.send_message("❌ Nenhum canal foi selecionado.", ephemeral=True)
            return

        try:
            cor = Color(int(self.cor_hex.value.lstrip('#'), 16)) if self.cor_hex.value else Color.blurple()
        except:
            cor = Color.blurple()

        embed = Embed(
            title=self.titulo.value,
            description=self.descricao.value,
            color=cor
        )

        # Posição da imagem
        posicao = self.posicao_imagem.value.lower() if self.posicao_imagem.value else "imagem"
        if self.imagem_url.value:
            if posicao == "thumbnail":
                embed.set_thumbnail(url=self.imagem_url.value)
            elif posicao == "footer":
                embed.set_footer(text="⠀", icon_url=self.imagem_url.value)
            else:
                embed.set_image(url=self.imagem_url.value)

        user_embed_data[interaction.user.id] = {
            "embed": embed,
            "canal": canal
        }

        await interaction.response.send_message("👀 Veja como seu embed vai ficar:", embed=embed, view=ConfirmEmbedView(interaction.user.id), ephemeral=True)

# View de confirmação
def is_same_user(interaction: Interaction, user_id):
    return interaction.user.id == user_id

class ConfirmEmbedView(ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id

    @ui.button(label="✅ Enviar", style=ButtonStyle.green)
    async def enviar(self, interaction: Interaction, button: ui.Button):
        if not is_same_user(interaction, self.user_id):
            await interaction.response.send_message("❌ Esse botão não é pra você!", ephemeral=True)
            return

        data = user_embed_data.get(self.user_id)
        if not data:
            await interaction.response.send_message("❌ Nada para enviar.", ephemeral=True)
            return
        await data["canal"].send(embed=data["embed"])
        await interaction.response.send_message("✅ Embed enviado com sucesso!", ephemeral=True)
        del user_embed_data[self.user_id]

    @ui.button(label="❌ Cancelar", style=ButtonStyle.red)
    async def cancelar(self, interaction: Interaction, button: ui.Button):
        if not is_same_user(interaction, self.user_id):
            await interaction.response.send_message("❌ Esse botão não é pra você!", ephemeral=True)
            return

        if self.user_id in user_embed_data:
            del user_embed_data[self.user_id]
        await interaction.response.send_message("🚫 Criação de embed cancelada.", ephemeral=True)

# Menu de seleção de canal
class ChannelSelect(ui.Select):
    def __init__(self, options, canais, bot):
        super().__init__(placeholder="Selecione o canal para enviar o embed...", options=options)
        self.canais = canais
        self.bot = bot

    async def callback(self, interaction: Interaction):
        canal = self.bot.get_channel(int(self.values[0]))
        self.canais[interaction.user.id] = canal
        await interaction.response.send_modal(EmbedCreatorModal(self.canais))

class ChannelSelectView(ui.View):
    def __init__(self, bot, ctx):
        super().__init__(timeout=60)
        self.bot = bot
        self.ctx = ctx
        self.canais = {}

        options = [
            SelectOption(label=canal.name, value=str(canal.id))
            for canal in ctx.guild.text_channels if canal.permissions_for(ctx.author).send_messages
        ]
        self.add_item(ChannelSelect(options, self.canais, bot))

# Comando para abrir o painel
@bot.command(name="embedpainel")
@commands.has_permissions(administrator=True)
async def painel_embed(ctx):
    await ctx.send("🧾 Selecione o canal onde o embed será enviado:", view=ChannelSelectView(bot, ctx))








bot.run('')