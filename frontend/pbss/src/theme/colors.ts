// Color palette configuration
// Easily updatable color system

export const colors = {
  brickRed: '#c1121fff',
  brilliantAzure: '#3083DCFF',
  lightAzure: '#a8cbf0ff',
  dustyGrape: '#4E4187FF',
  lightYellow: '#F8FFE5FF',
  lightGreen: '#7DDE92FF',
  oceanMist: '#2EBFA5FF',
} as const;

// Semantic color mappings
export const theme = {
  primary: colors.brilliantAzure,
  primaryLight: colors.brilliantAzure,
  secondary: colors.lightGreen,
  secondaryDark: colors.oceanMist,
  background: colors.lightYellow,
  text: {
    primary: colors.dustyGrape,
    secondary: '#2c3e50',
    inverse: colors.lightYellow,
  },
  border: colors.brilliantAzure,
  error: colors.brickRed,
  success: '#27ae60',
  warning: '#f39c12',
} as const;

