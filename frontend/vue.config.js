module.exports = {
  devServer: {
    public: "localhost:8081"
  },
  productionSourceMap: false,
  chainWebpack: config => {
    if (process.env.NODE_ENV === 'test') {
      const sassRule = config.module.rule('sass')
      sassRule.uses.clear()
      sassRule.use('null-loader').loader('null-loader')
    }
  },
  lintOnSave: false,
};
