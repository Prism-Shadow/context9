export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const copyToClipboard = async (text: string): Promise<boolean> => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    console.error('Failed to copy:', err);
    return false;
  }
};

export interface ParsedGitHubUrl {
  owner: string;
  repo: string;
  branch?: string;
  rootSpecPath?: string;
}

export const parseGitHubUrl = (url: string): ParsedGitHubUrl | null => {
  if (!url || !url.trim()) {
    return null;
  }

  try {
    // Remove whitespace
    url = url.trim();

    // Handle different GitHub URL formats
    // https://github.com/owner/repo
    // https://github.com/owner/repo/tree/branch
    // https://github.com/owner/repo/tree/branch/path/to/file
    // https://github.com/owner/repo/blob/branch/path/to/file
    // https://github.com/owner/repo.git
    // git@github.com:owner/repo.git

    let match: RegExpMatchArray | null = null;

    // Standard HTTPS GitHub URL
    match = url.match(/^https?:\/\/github\.com\/([^\/]+)\/([^\/\?#]+)/);
    if (match) {
      const owner = match[1];
      let repo = match[2];
      
      // Remove .git suffix if present
      if (repo.endsWith('.git')) {
        repo = repo.slice(0, -4);
      }

      const result: ParsedGitHubUrl = { owner, repo };

      // Try to extract branch and path
      // Match /tree/branch or /blob/branch
      const treeMatch = url.match(/\/tree\/([^\/]+)(?:\/(.+))?$/);
      const blobMatch = url.match(/\/blob\/([^\/]+)(?:\/(.+))?$/);
      
      if (blobMatch) {
        // blob URLs always point to a file
        result.branch = blobMatch[1];
        if (blobMatch[2]) {
          const path = decodeURIComponent(blobMatch[2]).replace(/\/$/, '');
          if (path) {
            result.rootSpecPath = path;
          }
        }
      } else if (treeMatch) {
        // tree URLs can point to a directory or file
        result.branch = treeMatch[1];
        if (treeMatch[2]) {
          let path = decodeURIComponent(treeMatch[2]).replace(/\/$/, '');
          // Only extract if it looks like a file path (last part has an extension)
          if (path) {
            const parts = path.split('/');
            const lastPart = parts[parts.length - 1];
            // Check if last part looks like a file (contains a dot and is not just a dot)
            if (lastPart.includes('.') && lastPart !== '.' && lastPart !== '..' && lastPart.split('.').length > 1) {
              result.rootSpecPath = path;
            }
          }
        }
      }

      return result;
    }

    // SSH format: git@github.com:owner/repo.git
    match = url.match(/^git@github\.com:([^\/]+)\/([^\/\?#]+)/);
    if (match) {
      const owner = match[1];
      let repo = match[2];
      
      // Remove .git suffix if present
      if (repo.endsWith('.git')) {
        repo = repo.slice(0, -4);
      }

      return { owner, repo };
    }

    return null;
  } catch (error) {
    console.error('Failed to parse GitHub URL:', error);
    return null;
  }
};
