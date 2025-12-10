# AI Co-Author Canvas

A dual-pane collaborative workspace for writing code and stories with AI assistance. Built with React, TypeScript, Vite, and Tailwind CSS.

![AI Co-Author Canvas](https://img.shields.io/badge/React-18.3.1-blue) ![TypeScript](https://img.shields.io/badge/TypeScript-5.6.2-blue) ![Vite](https://img.shields.io/badge/Vite-6.0.5-purple) ![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4.17-cyan)

## Features

- **Dual-Pane Interface**: Split screen with editor on the left and AI chat on the right
- **Two Modes**: Switch between Code (Developer) and Story (Writer) modes
- **AI Integration**: Supports OpenAI and Google Gemini APIs
- **Real-time Collaboration**: Chat with AI about your code or story
- **Smart Actions**: Insert AI responses directly at cursor position or copy to clipboard
- **Local Storage**: API keys stored securely in browser localStorage
- **Demo Mode**: Try the app without an API key
- **Download**: Export your work as .js or .md files

## Quick Start

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:5173`

### Build for Production

```bash
# Build the app
npm run build

# Preview production build
npm run preview
```

## Configuration

### Setting up AI API Keys

The app supports two AI provider types with flexible configuration:

#### Google Gemini

1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click the Settings icon in the app
3. Select "Google Gemini"
4. Configure (all optional except API Key):
   - **Base URL**: Custom Gemini endpoint (default: `generativelanguage.googleapis.com`)
   - **Model Name**: Model identifier (default: `gemini-2.0-flash-exp`)
   - **API Key**: Your Gemini API key (required)
5. Click "Save Configuration"

#### OpenAI Compatible APIs

Supports OpenAI, Claude, local models, and any OpenAI-compatible endpoints.

1. Get your API key from your provider:
   - [OpenAI Platform](https://platform.openai.com/api-keys)
   - [Anthropic Console](https://console.anthropic.com/)
   - Or your custom OpenAI-compatible service
2. Click the Settings icon in the app
3. Select "OpenAI Compatible"
4. Configure (all optional except API Key):
   - **Base URL**: API endpoint without `https://` (default: `api.openai.com`)
   - **Model Name**: Model identifier (default: `gpt-4o`)
   - **API Key**: Your API key (required)
5. Click "Save Configuration"

#### URL Parameters (Optional)

You can pass configuration via URL for quick setup:

```bash
# Google Gemini with defaults
http://localhost:5173?key=YOUR_API_KEY&provider=gemini

# Google Gemini with custom model
http://localhost:5173?key=YOUR_KEY&provider=gemini&model_name=gemini-1.5-pro

# OpenAI with defaults
http://localhost:5173?key=YOUR_API_KEY&provider=openai

# Custom OpenAI-compatible endpoint
http://localhost:5173?key=YOUR_KEY&provider=openai&base_url=api.anthropic.com&model_name=claude-3-opus-20240229

# Local model
http://localhost:5173?key=dummy&provider=openai&base_url=localhost:8000&model_name=llama-3
```

## Usage

### Code Mode

- Write and edit code in the left pane
- Use monospace font optimized for coding
- Ask AI to generate functions, debug, or explain code
- Download as `.js` file

### Story Mode

- Write prose in the left pane with a serif font
- Get AI help with character development, plot ideas, or continuations
- Download as `.md` file

### AI Chat Features

- **Send Message**: Type your request and press Enter or click Send
- **Insert at Cursor**: Click "Insert" to add AI response at your cursor position
- **Copy**: Copy AI responses to clipboard
- **Context-Aware**: AI sees your current canvas content

## Project Structure

```
canvas-frontend/
├── src/
│   ├── App.tsx          # Main application component
│   ├── main.tsx         # Application entry point
│   ├── index.css        # Global styles with Tailwind
│   └── vite-env.d.ts    # TypeScript definitions
├── index.html           # HTML template
├── package.json         # Dependencies and scripts
├── tsconfig.json        # TypeScript configuration
├── vite.config.ts       # Vite configuration
├── tailwind.config.js   # Tailwind CSS configuration
└── postcss.config.js    # PostCSS configuration
```

## Tech Stack

- **React 18.3.1**: UI framework
- **TypeScript 5.6.2**: Type safety
- **Vite 6.0.5**: Fast build tool and dev server
- **Tailwind CSS 3.4.17**: Utility-first CSS framework
- **Lucide React**: Beautiful icon library
- **OpenAI/Gemini API**: AI-powered assistance

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### TypeScript Configuration

The project uses strict TypeScript settings for better type safety. Check `tsconfig.json` for details.

### Styling

Tailwind CSS is configured with custom animations. Modify `tailwind.config.js` to customize the theme.

## Privacy & Security

- API keys are stored only in your browser's localStorage
- No data is sent to our servers
- All AI requests go directly to OpenAI or Google
- You can clear your API key anytime in Settings

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Troubleshooting

### Development server won't start
- Make sure port 5173 is not in use
- Delete `node_modules` and run `npm install` again

### API not working
- Check your API key in Settings
- Verify you have API credits/quota
- Check browser console for errors

### Styles not loading
- Make sure Tailwind is properly configured
- Run `npm run build` to regenerate CSS

## License

MIT License - feel free to use this project for personal or commercial purposes.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

---

Built with ❤️ using React, TypeScript, and Tailwind CSS
