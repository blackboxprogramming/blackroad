const withMDX = require('@next/mdx')({
  extension: /\.(mdx?)$/.source ? undefined : /\.(mdx?)$/, // placeholder to satisfy require, not necessary
});
module.exports = withMDX({
  pageExtensions: ['js', 'jsx', 'ts', 'tsx', 'md', 'mdx'],
});
