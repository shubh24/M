console.log('Hello World');


Urls = new Mongo.Collection('urls');
Lines = new Mongo.Collection('lines');

if (Meteor.isClient){
	Template.summary.events({
		'submit form':function(event){
		var searchUser = event.target.searchUser.value;
		$('#searchUser').val("");
		Session.set('urlFound',searchUser);

	    Meteor.call('callPython', searchUser, function(err,lol){
	        Session.set('lol',lol);
	    });

	    return false
	  }
	})

	Template.results.helpers({
		'res' : function(){
	    	return Session.get('lol');
	    }
	});


}

if (Meteor.isServer){


    Meteor.methods({

        'callPython' : function(url){
			Future = Npm.require('fibers/future');
        	var future = new Future();
            var childProcess = Meteor.npmRequire('child_process');
            console.log('gt')
            file_path = '/home/shubhankar/Desktop/summarize.py';
            childProcess.exec("python " + file_path + ' 1 ' + url + ' 5', function(error, stdout, stderr) {
                console.log(stdout);
                future['return'](stdout);
            });

			return future.wait();

        }

    });

}

