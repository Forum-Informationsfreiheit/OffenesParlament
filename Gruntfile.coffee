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
          'offenesparlament/offenesparlament/static/scripts/app.js': 'offenesparlament/offenesparlament/assets/scripts/app.coffee'
    concat:
      vendor:
        src: ['offenesparlament/offenesparlament/assets/scripts/vendor/visualsearch/dependencies.js', 'offenesparlament/offenesparlament/assets/scripts/vendor/visualsearch/visualsearch.js']
        dest: 'offenesparlament/offenesparlament/static/scripts/vendor.js'
    sass:
      dev:
        options:
          sourcemap: 'inline'
        files:
          'offenesparlament/offenesparlament/static/css/vendor.css': 'offenesparlament/offenesparlament/assets/styles/vendor/vendor.sass'
          'offenesparlament/offenesparlament/static/css/site.css': 'offenesparlament/offenesparlament/assets/styles/site.sass'
    watch:
      styles:
        files: 'offenesparlament/offenesparlament/assets/styles/**/*'
        tasks: [ 'clean:style_images', 'build_styles' ]
      scripts:
        files: 'offenesparlament/offenesparlament/assets/scripts/**/*'
        tasks: [ 'browserify:dev' ]
    browserSync:
      dev:
        bsFiles:
          src : [
            'offenesparlament/offenesparlament/**/*'
            '!**/*.sqlite3'
            '!**/*.map'
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
        cwd: 'offenesparlament/offenesparlament/assets/styles/'
        src: [ 'img/**/*' ]
        dest: 'offenesparlament/offenesparlament/static/css/'
        expand: true
      fonts:
        cwd: 'offenesparlament/offenesparlament/assets/styles/'
        src: [ 'fonts/**/*' ]
        dest: 'offenesparlament/offenesparlament/static/'
        expand: true
      vendor_scripts:
        cwd: 'offenesparlament/offenesparlament/assets/scripts/vendor'
        src: [ 'search.js' ]
        dest: 'offenesparlament/offenesparlament/static/scripts/'
        expand: true
    clean:
      build: src: [
        'offenesparlament/offenesparlament/static/css/vendor.css'
        'offenesparlament/offenesparlament/static/css/site.css'
        'offenesparlament/offenesparlament/static/scripts/app.js'
      ]
      style_images: src: 'offenesparlament/offenesparlament/static/css/img'
      style_fonts: src: 'offenesparlament/offenesparlament/static/fonts'
      scripts: src: 'offenesparlament/offenesparlament/static/scripts'


  grunt.loadNpmTasks 'grunt-contrib-watch'
  grunt.loadNpmTasks 'grunt-browser-sync'
  grunt.loadNpmTasks 'grunt-contrib-clean'
  grunt.loadNpmTasks 'grunt-contrib-sass'
  grunt.loadNpmTasks 'grunt-contrib-copy'
  grunt.loadNpmTasks 'grunt-contrib-concat'
  grunt.loadNpmTasks 'grunt-browserify'

  grunt.registerTask 'build_styles', ['sass:dev', 'copy:images', 'copy:fonts']
  grunt.registerTask 'dev', ['clean', 'build_styles', 'browserify:dev', 'concat:vendor', 'watch']
  grunt.registerTask 'reloading', ['clean', 'build_styles', 'browserify:dev', 'concat:vendor', 'browserSync', 'watch']

