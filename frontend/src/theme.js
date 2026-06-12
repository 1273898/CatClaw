import { createTheme } from '@mui/material/styles'

// 浅粉色主题
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#f48fb1', // 浅粉色
      light: '#f8bbd0',
      dark: '#ec407a',
      contrastText: '#fff',
    },
    secondary: {
      main: '#ce93d8', // 淡紫色
      light: '#e1bee7',
      dark: '#ab47bc',
      contrastText: '#fff',
    },
    background: {
      default: '#1a1a2e', // 深色背景
      paper: '#16213e',
    },
    text: {
      primary: '#f5f5f5',
      secondary: '#b0b0b0',
    },
    divider: 'rgba(244, 143, 177, 0.2)',
    error: {
      main: '#ef5350',
    },
    warning: {
      main: '#ffa726',
    },
    info: {
      main: '#42a5f5',
    },
    success: {
      main: '#66bb6a',
    },
  },
  typography: {
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    h1: {
      fontSize: '2rem',
      fontWeight: 600,
    },
    h2: {
      fontSize: '1.5rem',
      fontWeight: 600,
    },
    h3: {
      fontSize: '1.25rem',
      fontWeight: 600,
    },
    body1: {
      fontSize: '0.875rem',
    },
    body2: {
      fontSize: '0.8125rem',
    },
    button: {
      textTransform: 'none',
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 16px',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          border: '1px solid rgba(244, 143, 177, 0.2)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
          },
        },
      },
    },
  },
})

export default theme
