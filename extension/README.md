# CodeMedic 🩺

[![Visual Studio Marketplace](https://img.shields.io/visual-studio-marketplace/v/gerardosanchezz.codemedic.svg)](https://marketplace.visualstudio.com/items?itemName=gerardosanchezz.codemedic)
[![Downloads](https://img.shields.io/visual-studio-marketplace/d/gerardosanchezz.codemedic.svg)](https://marketplace.visualstudio.com/items?itemName=gerardosanchezz.codemedic)
[![Rating](https://img.shields.io/visual-studio-marketplace/r/gerardosanchezz.codemedic.svg)](https://marketplace.visualstudio.com/items?itemName=gerardosanchezz.codemedic)

A VS Code extension designed to assist developers in managing and resolving GitHub issues directly within their development environment. CodeMedic streamlines the issue-handling process by integrating with GitHub repositories, allowing developers to either receive a guided solution or apply an automated fix.

**AI-powered GitHub issue resolver with ReactAgent integration**

CodeMedic revolutionizes how developers handle GitHub issues by combining the power of AI with seamless VS Code integration. Automatically analyze, understand, and fix issues using advanced language models running on Modal's cloud infrastructure.

## ✨ Features

### 🤖 **AI-Powered Issue Resolution**
- **ReactAgent Integration**: Uses advanced ReAct (Reasoning + Acting) pattern for intelligent problem-solving
- **HuggingFace Models**: Powered by Qwen/Qwen3-4B model for code understanding and generation
- **GPU Processing**: Runs on Modal's cloud infrastructure with L4 GPU support

### 📋 **GitHub Integration**
- **Issue Management**: View and manage GitHub issues directly in VS Code
- **Repository Detection**: Automatically detects GitHub repositories in your workspace
- **Authentication**: Secure GitHub token-based authentication

### 🛠️ **Smart Code Analysis**
- **Context Awareness**: Analyzes repository structure and codebase
- **Pattern Recognition**: Identifies common bug patterns and solutions
- **Automated Fixes**: Generates intelligent code fixes and patches

### 🎯 **Developer Experience**
- **Side Panel Integration**: Dedicated views for issues and agent responses
- **Real-time Processing**: Live updates during issue resolution
- **Detailed Responses**: Step-by-step explanation of the fixing process

## 🚀 Getting Started

### Installation
1. Install the extension from the VS Code Marketplace
2. Open a project with a GitHub repository
3. Click the CodeMedic icon in the activity bar
4. Authenticate with your GitHub account

### First Time Setup
1. **GitHub Authentication**: Generate a personal access token with repo permissions
2. **Repository Access**: Ensure your repository has issues enabled
3. **Issue Selection**: Choose any open issue to start the resolution process

## 📖 How to Use

### Step 1: Open Issues Panel
Click on the CodeMedic icon in the activity bar to view all GitHub issues from your repository.

### Step 2: Select an Issue
Click on any issue to view its details in a dedicated panel.

### Step 3: AI Resolution
Click "Fix this issue with CodeMedic" to start the AI-powered resolution process.

### Step 4: Review Results
View the AI agent's analysis and proposed solution in the Agent Responses panel.

## 🔧 Requirements

- **VS Code**: Version 1.74.0 or higher
- **GitHub Repository**: A repository with issues
- **Internet Connection**: For AI processing on Modal cloud
- **GitHub Token**: Personal access token with repository permissions

## ⚙️ Configuration

The extension works **completely out of the box** with no additional configuration required!

### 🔧 **How it works:**
- **Backend**: Runs on Modal cloud infrastructure
- **AI Models**: Uses HuggingFace models (Qwen/Qwen3-4B)
- **Authentication**: Only requires GitHub personal access token
- **Processing**: All AI processing happens on Modal's GPU servers

### 📋 **Required setup:**
1. **GitHub Token**: Generated through the extension's authentication flow
2. **Internet Connection**: For Modal cloud processing
3. **Repository**: Any GitHub repository with issues

### 🚫 **No additional API keys needed:**
- ❌ No OpenAI API key required
- ❌ No HuggingFace token needed from users
- ❌ No Modal account required for users
- ✅ Everything is pre-configured and ready to use!

## 🏗️ Architecture

CodeMedic uses a modern, scalable architecture:

- **Frontend**: VS Code extension with TypeScript
- **Backend**: FastAPI on Modal cloud platform
- **AI Engine**: ReactAgent with HuggingFace models
- **Infrastructure**: GPU-accelerated processing on Modal

## 🎯 Use Cases

### Perfect for:
- **Bug Fixes**: Automatic identification and resolution of common bugs
- **Code Issues**: Syntax errors, logic problems, and performance issues
- **Documentation**: Missing or incorrect documentation updates
- **Feature Requests**: Implementation guidance for new features

### Example Issues CodeMedic Can Handle:
- Syntax errors in various programming languages
- Missing error handling
- Performance optimization opportunities
- Code style and formatting issues
- Documentation updates

## 🛡️ Privacy & Security

- **Secure Processing**: All code analysis happens on secure Modal infrastructure
- **No Data Storage**: Your code is not permanently stored
- **GitHub Integration**: Uses standard OAuth authentication
- **Open Source**: Transparent and auditable codebase

## 🔄 Release Notes

### 1.0.0 - Initial Release
- ✅ GitHub issue integration
- ✅ ReactAgent AI processing
- ✅ Modal cloud deployment
- ✅ Real-time issue resolution
- ✅ Detailed response visualization

## 🐛 Known Issues

- Large repositories may take longer to process
- Complex multi-file issues require manual review
- Network connectivity required for AI processing

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](https://github.com/CarlosVP120/CodeMedic/blob/main/CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/CarlosVP120/CodeMedic/issues)
- **Documentation**: [Project Wiki](https://github.com/CarlosVP120/CodeMedic/wiki)
- **Email**: support@codemedic.dev

## 🌟 Acknowledgments

- **Modal**: For providing the cloud infrastructure
- **HuggingFace**: For the AI models
- **LangGraph**: For the ReactAgent framework
- **VS Code Team**: For the excellent extension API

---

**Made with ❤️ by developers, for developers**

*Transform your GitHub workflow with AI-powered issue resolution. Try CodeMedic today!*
