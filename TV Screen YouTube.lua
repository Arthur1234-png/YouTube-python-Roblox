local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")

-- Procura o modelo e a peça exatamente com os nomes que você passou
local FlatScreenTV = workspace:WaitForChild("Flat Screen TV")
local ScreenPart = FlatScreenTV:WaitForChild("Screen")

-- ⚠️ Substitua com o endereço do seu servidor Python (Render, Koyeb ou IP Local)
local URL_BASE = "http://seu-servidor-python.com"

-- Configurações da matriz de pixels (Devem ser iguais às do Python)
local LARGURA = 32
local ALTURA = 24

local tocandoVideo = false
local framesCache = {}

-- 1. Garante que a SurfaceGui exista na peça Screen e inicializa os pixels
local function inicializarTelaVirtual()
	local surfaceGui = ScreenPart:FindFirstChildOfClass("SurfaceGui")
	
	-- Se não existir uma SurfaceGui na peça Screen, o script cria uma perfeita
	if not surfaceGui then
		surfaceGui = Instance.new("SurfaceGui")
		surfaceGui.Name = "TvSurfaceGui"
		surfaceGui.Face = Enum.NormalId.Front -- Ajuste a face (Front, Back, etc) se a imagem ficar atrás da TV
		surfaceGui.CanvasSize = Vector2.new(800, 600) -- Resolução interna da interface
		surfaceGui.AlwaysOnTop = false
		surfaceGui.LightInfluence = 0 -- Faz a tela brilhar no escuro como uma TV de verdade
		surfaceGui.Parent = ScreenPart
	end
	
	-- Limpa o Canvas antigo se existir para não acumular lixo
	local canvas = surfaceGui:FindFirstChild("VideoCanvas")
	if canvas then canvas:Destroy() end
	
	canvas = Instance.new("Frame")
	canvas.Name = "VideoCanvas"
	canvas.Size = UDim2.new(1, 0, 1, 0)
	canvas.BackgroundTransparency = 1
	canvas.Parent = surfaceGui
	
	-- Distribuidor em Grade para alinhar os pixels perfeitamente
	local gridLayout = Instance.new("UIGridLayout")
	gridLayout.CellSize = UDim2.new(1 / LARGURA, 0, 1 / ALTURA, 0)
	gridLayout.CellPadding = UDim2.new(0, 0, 0, 0)
	gridLayout.SortOrder = Enum.SortOrder.Name
	gridLayout.Parent = canvas
	
	-- Cria os pequenos Frames que fingem ser os pixels do vídeo
	for y = 1, ALTURA do
		for x = 1, LARGURA do
			local pixelFrame = Instance.new("Frame")
			-- Nome formatado em ordem (ex: "01_05") para o UIGridLayout não embaralhar as linhas
			pixelFrame.Name = string.format("%02d_%02d", y, x)
			pixelFrame.BorderSizePixel = 0
			pixelFrame.BackgroundColor3 = Color3.fromRGB(0, 0, 0)
			pixelFrame.Parent = canvas
			
			-- Guarda no cache para o atualizador encontrar instantaneamente sem dar lag
			framesCache[x .. "_" .. y] = pixelFrame
		end
	end
end

inicializarTelaVirtual()

-- 2. Interface de Usuário Automática (TextBox + Botão de Tocar na tela de quem joga)
local function criarInterface(player)
	local playerGui = player:WaitForChild("PlayerGui")
	if playerGui:FindFirstChild("VideoPlayerGui") then playerGui.VideoPlayerGui:Destroy() end
	
	local screenGui = Instance.new("ScreenGui")
	screenGui.Name = "VideoPlayerGui"
	screenGui.ResetOnSpawn = false
	
	local textBox = Instance.new("TextBox")
	textBox.Name = "UrlInput"
	textBox.Size = UDim2.new(0, 350, 0, 40)
	textBox.Position = UDim2.new(0.5, -230, 0.85, 0)
	textBox.BackgroundColor3 = Color3.fromRGB(30, 30, 30)
	textBox.TextColor3 = Color3.fromRGB(255, 255, 255)
	textBox.PlaceholderText = "Cole a URL do YouTube aqui..."
	textBox.PlaceholderColor3 = Color3.fromRGB(150, 150, 150)
	textBox.Font = Enum.Font.SourceSans
	textBox.TextSize = 18
	textBox.Text = ""
	textBox.ClearTextOnFocus = false
	textBox.Parent = screenGui
	
	local button = Instance.new("TextButton")
	button.Name = "BotaoTocar"
	button.Size = UDim2.new(0, 100, 0, 40)
	button.Position = UDim2.new(0.5, 130, 0.85, 0)
	button.BackgroundColor3 = Color3.fromRGB(0, 170, 255)
	button.TextColor3 = Color3.fromRGB(255, 255, 255)
	button.Text = "Tocar"
	button.Font = Enum.Font.SourceSansBold
	button.TextSize = 18
	button.Parent = screenGui
	
	screenGui.Parent = playerGui
	
	local carregando = false
	button.MouseButton1Click:Connect(function()
		if carregando then return end
		
		local url = textBox.Text
		if url ~= "" and (string.find(url, "youtube.com") or string.find(url, "youtu.be")) then
			carregando = true
			button.Text = "Baixando..."
			button.BackgroundColor3 = Color3.fromRGB(120, 120, 120)
			
			local dadosEnvio = HttpService:JSONEncode({["url"] = url})
			local sucesso, resultado = pcall(function()
				return HttpService:PostAsync(URL_BASE .. "/carregar-video", dadosEnvio, Enum.HttpContentType.ApplicationJson)
			end)
			
			carregando = false
			button.Text = "Tocar"
			button.BackgroundColor3 = Color3.fromRGB(0, 170, 255)
			
			if sucesso then
				local resposta = HttpService:JSONDecode(resultado)
				if resposta.status == "sucesso" then
					tocandoVideo = true
					textBox.Text = resposta.mensagem
				else
					textBox.Text = "Erro no processamento do vídeo."
				end
			else
				textBox.Text = "Erro: Servidor Python offline!"
			end
		else
			textBox.Text = ""
			textBox.PlaceholderText = "Insira um link válido do YouTube!"
		end
	end)
end

Players.PlayerAdded:Connect(criarInterface)

-- 3. Renderizador de Cores da UI
local function desenharMatriz(dadosFrame)
	local pixels = dadosFrame.pixels
	local largura = dadosFrame.largura
	local altura = dadosFrame.altura
	
	local index = 1
	for y = 1, altura do
		for x = 1, largura do
			local r = pixels[index] / 255
			local g = pixels[index + 1] / 255
			local b = pixels[index + 2] / 255
			index = index + 3
			
			local pixelFrame = framesCache[x .. "_" .. y]
			if pixelFrame then
				pixelFrame.BackgroundColor3 = Color3.new(r, g, b)
			end
		end
	end
end

-- 4. Motor assíncrono de requisição de frames (Loop de Vídeo)
task.spawn(function()
	while true do
		if tocandoVideo then
			local sucesso, resultado = pcall(function()
				return HttpService:GetAsync(URL_BASE .. "/proximo-frame")
			end)
			
			if success and resultado then
				local dadosFrame = HttpService:JSONDecode(resultado)
				desenharMatriz(dadosFrame)
			else
				warn("Aguardando fluxo de frames da Flat Screen TV...")
			end
		end
		-- Taxa de atualização estável para evitar sobrecarga de HTTP
		task.wait(0.03)
	end
end)
