module.exports = (grunt) ->

  # configure the tasks
  grunt.initConfig
    sass:
      dev:
        options:
          sourcemap: 'inline'
        files:
          'offenesparlament/offenesparlament/static/css/vendor.css': 'offenesparlament/offenesparlament/assets/styles/bootstrap.css'
          'offenesparlament/offenesparlament/static/css/site.css': 'offenesparlament/offenesparlament/assets/styles/site.sass'
    watch:
      styles:
        files: 'offenesparlament/offenesparlament/assets/styles/**/*'
        tasks: [ 'sass:dev' ]
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
    clean:
      build: src: ['offenesparlament/offenesparlament/static/css/vendor.css',
                   'offenesparlament/offenesparlament/static/css/site.css']


  grunt.loadNpmTasks 'grunt-contrib-watch'
  grunt.loadNpmTasks 'grunt-browser-sync'
  grunt.loadNpmTasks 'grunt-contrib-clean'
  grunt.loadNpmTasks 'grunt-contrib-sass'

  grunt.registerTask 'dev', ['clean', 'sass:dev', 'watch']
  grunt.registerTask 'reloading', ['clean', 'sass:dev', 'browserSync', 'watch']

