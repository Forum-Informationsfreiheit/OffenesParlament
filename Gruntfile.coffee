module.exports = (grunt) ->

  # configure the tasks
  grunt.initConfig
    browserify:
      options:
        debug: true
        transform: ['coffee-reactify']
        extensions: ['.jsx', '.cjsx', '.coffee']
      dev:
        options:
          alias: ['react:']  # Make React available externally for dev tools
        files:
          'offenesparlament/offenesparlament/static/scripts/app.js': 'client/scripts/app.coffee'
          'offenesparlament/offenesparlament/static/scripts/homepage.js': 'client/scripts/homepage.coffee'
    sass:
      dev:
        options:
          sourcemap: 'inline'
        files:
          'offenesparlament/offenesparlament/static/css/vendor.css': 'client/styles/vendor/vendor.sass'
          'offenesparlament/offenesparlament/static/css/site.css': 'client/styles/site.sass'
          'offenesparlament/offenesparlament/static/css/email.css': 'client/styles/emails/base.sass'
    watch:
      styles:
        files: 'client/styles/**/*'
        tasks: [ 'clean:style_images', 'build_styles' ]
      scripts:
        files: 'client/scripts/**/*'
        tasks: [ 'browserify:dev' ]
    browserSync:
      dev:
        bsFiles:
          src : [
            'offenesparlament/offenesparlament/**/*'
            '!offenesparlament/offenesparlament/static/fonts/**/*'
            '!**/*.sqlite3'
            '!**/*.map'
            '!**/*.DS_Store'
          ]
        options:
          watchTask: true
          proxy: 'offenesparlament.vm:8000'
          ghostMode: false
          open: false
          reloadOnRestart: false
          reloadDebounce: 1000
    copy:
      images:
        cwd: 'client/styles/'
        src: [ 'img/**/*' ]
        dest: 'offenesparlament/offenesparlament/static/css/'
        expand: true
      fonts:
        cwd: 'client/styles/'
        src: [ 'fonts/**/*' ]
        dest: 'offenesparlament/offenesparlament/static/'
        expand: true
    clean:
      build: src: [
        'offenesparlament/offenesparlament/static/css'
        'offenesparlament/offenesparlament/static/scripts/app.js'
      ]
      style_images: src: 'offenesparlament/offenesparlament/static/css/img'
      style_fonts: src: 'offenesparlament/offenesparlament/static/fonts'
      scripts: src: 'offenesparlament/offenesparlament/static/scripts'
      favicons: src: 'offenesparlament/offenesparlament/static/favicons'
    favicons:
      options:
        androidHomescreen: true
        trueColor: true
        precomposed: true
        appleTouchBackgroundColor: "#ffffff"
        coast: true
        windowsTile: true
        tileBlackWhite: false
        tileColor: "#ffffff"
      icons:
        src: 'client/styles/img/favicon.png'
        dest: 'offenesparlament/offenesparlament/static/favicons/'


  grunt.loadNpmTasks 'grunt-contrib-watch'
  grunt.loadNpmTasks 'grunt-browser-sync'
  grunt.loadNpmTasks 'grunt-contrib-clean'
  grunt.loadNpmTasks 'grunt-contrib-sass'
  grunt.loadNpmTasks 'grunt-contrib-copy'
  grunt.loadNpmTasks 'grunt-contrib-concat'
  grunt.loadNpmTasks 'grunt-browserify'
  grunt.loadNpmTasks 'grunt-favicons'

  grunt.registerTask 'build_styles', ['sass:dev', 'copy:images', 'copy:fonts']
  grunt.registerTask 'clean_except_icons', [ 'clean:build', 'clean:style_images', 'clean:style_fonts', 'clean:scripts' ]
  grunt.registerTask 'icons', ['favicons:icons']
  grunt.registerTask 'dev', ['clean_except_icons', 'build_styles', 'browserify:dev', 'watch']
  grunt.registerTask 'reloading', ['clean_except_icons', 'build_styles', 'browserify:dev', 'browserSync', 'watch']

