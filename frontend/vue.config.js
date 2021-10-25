module.exports = {
  devServer: {
    public: 'localhost:8081',
    proxy: {
      '^/api': {
        target: 'http://localhost:8080'
      }
    }
  },
  chainWebpack: config => {
    config.module.rule('eslint').use('eslint-loader').options({
      fix: true
    })
  }
}
