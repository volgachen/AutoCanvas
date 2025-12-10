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

The app supports two AI providers:

#### Option 1: Google Gemini (Recommended for free tier)

1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click the Settings icon in the app
3. Select "Google Gemini"
4. Enter your API key
5. Click "Save Configuration"

#### Option 2: OpenAI

1. Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Click the Settings icon in the app
3. Select "OpenAI"
4. Enter your API key
5. Click "Save Configuration"

#### URL Parameters (Optional)

You can also pass API credentials via URL:

```
http://localhost:5173?key=YOUR_API_KEY&provider=gemini
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
