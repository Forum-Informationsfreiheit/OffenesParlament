module.exports = (grunt) ->

  # configure the tasks
  grunt.initConfig
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
    clean:
      build: src: ['offenesparlament/offenesparlament/static/css/vendor.css',
                   'offenesparlament/offenesparlament/static/css/site.css']
      style_images: src: 'offenesparlament/offenesparlament/static/css/img'
      style_fonts: src: 'offenesparlament/offenesparlament/static/fonts'


  grunt.loadNpmTasks 'grunt-contrib-watch'
  grunt.loadNpmTasks 'grunt-browser-sync'
  grunt.loadNpmTasks 'grunt-contrib-clean'
  grunt.loadNpmTasks 'grunt-contrib-sass'
  grunt.loadNpmTasks 'grunt-contrib-copy'

  grunt.registerTask 'build_styles', ['sass:dev', 'copy:images', 'copy:fonts']
  grunt.registerTask 'dev', ['clean', 'build_styles', 'watch']
  grunt.registerTask 'reloading', ['clean', 'build_styles', 'browserSync', 'watch']

