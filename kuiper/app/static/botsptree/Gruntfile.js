/* jshint node: true */

module.exports = function(grunt) {
  'use strict';

  // Project configuration.
  grunt.initConfig({

    // Metadata.
    pkg: grunt.file.readJSON('package.json'),
    banner: '/**\n' +
              '* <%= pkg.name %>.js v<%= pkg.version %> by @morrissinger\n' +
              '* Copyright <%= grunt.template.today("yyyy") %> <%= pkg.author %>\n' +
              '* <%= _.pluck(pkg.licenses, "url").join(", ") %>\n' +
              '*/\n',
    jqueryCheck: 'if (!jQuery) { throw new Error(\"Bootstrap Tree Nav requires jQuery\"); }\n\n',

    // Task configuration.
    clean: {
      dist: ['dist']
    },

    jshint: {
      options: {
        jshintrc: 'js/.jshintrc'
      },
      gruntfile: {
        src: 'Gruntfile.js'
      },
      src: {
        src: [
          'js/lang/*/*.js',
          'js/*.js'
        ]
      }
    },

    concat: {
      options: {
        banner: '<%= banner %><%= jqueryCheck %>',
        stripBanners: false
      },
      bootstraptreenav: {
        src: [
          'js/*.js'
        ],
        dest: 'dist/js/<%= pkg.name %>.js'
      }
    },

    uglify: {
      options: {
        banner: '<%= banner %>'
      },
      bootstraptreenav: {
        src: ['<%= concat.bootstraptreenav.dest %>'],
        dest: 'dist/js/<%= pkg.name %>.min.js'
      }
    },
   
    copy: {
      img: {
        expand: true,
        src: ['img/*'],
        dest: 'dist/'
      }
    },
    sass: {
      src: {
        options: {
          style: 'expanded',
          banner: '<%= banner %>'
        },
        files: {
          'dist/css/bootstrap-treenav.css' : 'sass/bootstrap-treenav.scss'
        }
      },
      dist: {
        options: {
          style: 'compressed',
          banner: '<%= banner %>'
        },
        files: {
          'dist/css/bootstrap-treenav.min.css' : 'sass/bootstrap-treenav.scss'
        }
      }
    },
    watch: {
      src: {
        files: '<%= jshint.src.src %>',
        tasks: ['jshint:src']
      },
      css: {
        files: '**/*.scss',
        tasks: ['sass']
      }
    }
  });


  // These plugins provide necessary tasks.
  grunt.loadNpmTasks('grunt-contrib-clean');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-contrib-jshint');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-sass');
  grunt.loadNpmTasks('grunt-contrib-watch');

  var testSubtasks = ['dist-css', 'jshint'];
  // Only push to coveralls under Travis
  if (process.env.TRAVIS) {
    if ((process.env.TRAVIS_REPO_SLUG === 'morrissinger/BootstrapTreeNav' && process.env.TRAVIS_PULL_REQUEST === 'false')) {
      testSubtasks.push('coveralls');
    }
  }
  grunt.registerTask('test', testSubtasks);

  // JS distribution task.
  grunt.registerTask('dist-js', ['concat', 'uglify']);

  // CSS distribution task.
  grunt.registerTask('dist-css', ['sass']);
  
  // Img distribution task.
  grunt.registerTask('dist-img', ['copy']);
  
  // Full distribution task.
  grunt.registerTask('dist', ['clean', 'dist-css', 'dist-img', 'dist-js']);

  // Default task.
  grunt.registerTask('default', ['test', 'dist']);
};