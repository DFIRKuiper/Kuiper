module.exports = function (grunt) {
    grunt.file.defaultEncoding = 'utf-8';

    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),
        // Delete generated files
        clean: {
            all: {
                src: [ 'dist/*.js', 'dist/*.css' ]
            }
        },

        // Compile less to css
        less: {
            compile: {
                files: {'dist/jquery.datetimepicker.css': 'src/jquery.datetimepicker.less'}
            }
        },

        // Compress css
        cssmin: {
            target: {
                files: [{
                    expand: true,
                    cwd: 'dist',
                    src: ['*.css', '!*.min.css'],
                    extDot: 'last',
                    dest: 'dist',
                    ext: '.min.css'
                }]
            }
        },

        // Compress javascript
        uglify: {
            product: {
                files: [{
                    // src
                    expand: true,
                    cwd: 'src',
                    extDot: 'last',
                    src: '*.js',
                    dest: 'dist',
                    ext: '.min.js'
                }, {
                    // lib
                    expand: true,
                    cwd: 'lib',
                    extDot: 'last',
                    src: '*.js',
                    dest: 'dist',
                    ext: '.min.js'
                }]
            }
        }
    });

    // Loads specified plug-in tasks
    grunt.loadNpmTasks('grunt-contrib-clean');
    grunt.loadNpmTasks('grunt-contrib-jshint');
    grunt.loadNpmTasks('grunt-contrib-concat');
    grunt.loadNpmTasks('grunt-contrib-copy');
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-contrib-less');
    grunt.loadNpmTasks('grunt-contrib-cssmin');

    // Grunt runner
    grunt.registerTask('default', [
        'clean:all',
        'less:compile',
        'cssmin',
        'uglify:product'
    ]);
};
