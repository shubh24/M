console.log('Hello World');

Tweets = new Mongo.Collection('tweets');
Relationships = new Mongo.Collection('relationships');

UserUtils = function() {};    //no var in front

UserUtils.findFollowings = function(username) {  
  var currentFollowings = Relationships.find({
    follower: username
  }).fetch().map(function(data) {
    return data.following;
  });
  currentFollowings.push(Meteor.user().username);

  return currentFollowings;
};


if(Meteor.isClient){
	Template.tweetBox.onRendered(function () {  
	  	Session.set('numChars', 0);
	});4

	Template.tweetBox.events({  
		  'input #tweetText': function(){
		    Session.set('numChars', $('#tweetText').val().length);
		  },
		  'click button' : function() {  
			  var tweet = $('#tweetText').val();
			  $('#tweetText').val("");
			  Session.set('numChars', 0);
			  Meteor.call('insertTweet',tweet);
		  }
	});

	Template.tweetBox.helpers({  
		  charCount: function() {
		    return 140 - Session.get('numChars');
		  },

		  charClass: function() {
		    if (Session.get('numChars') > 140) {
		      return 'errCharCount';    //css class name
		    } else {
		      return 'charCount';       //css class name
		    }
		  },

		  disableButton: function() {
		    if (Session.get('numChars') <= 0 ||
			Session.get('numChars') > 140 ||
			!Meteor.user()) {
		      return 'disabled';
		    }
		  }	
	});

	Template.userManagement.helpers({  
	  'tweets': function() {
	    if (Meteor.user()) {
	      return Tweets.find({ user: Meteor.user().username }).count();
	    }
	  },

	  'following': function() {
	    if (Meteor.user()) {
	      return Relationships.find({ follower: Meteor.user().username }).count();
	    }
	  },

	  'followers': function() {
	    if (Meteor.user()) {
	      return Relationships.find({ following: Meteor.user().username }).count();
	    }
	  }
	});

	

	Template.userManagement.events({  
	  'click #signup': function() {
	    var user = {
	      username: $('#signup-username').val(),
	      password: $('#signup-password').val(),
	      profile: {
		fullname: $('#signup-fullname').val()
	      }
	    };

	    Accounts.createUser(user, function (error) {
	      if(error) alert(error);
 	   	});
  	   },
	  'click #login': function() {
	    var username = $('#login-username').val();
	    var password = $('#login-password').val();

	    Meteor.loginWithPassword(username, password, function(error) {
	      if(error) alert(error);
	    });
	  },
	  'click #logout': function() {  
	  	Meteor.logout();
	  }
	});

	
	Template.userManagement.onCreated( function() {  
	  if (Meteor.user()) {
	    this.subscribe('followings', Meteor.user().username);
	    this.subscribe('followers', Meteor.user().username);
	    this.subscribe('tweets', Meteor.user().username);
	  }
	});

	Template.followUsers.events({
	  'submit form':function(event){
		var searchUser = event.target.searchUser.value;
		var foundUser = Meteor.call('findUser',searchUser, function(err,res){
			if (res) {Session.set('foundUser', res)}
			else{alert('User doesn\'t exist!')}
		});
		$('#searchUser').val("");
		return false;
	  },

	 'click #follow': function() {
	    Meteor.call('followUser', Session.get('foundUser').username);
	  },
	  'click #followRec': function(event) {
	    Meteor.call('followUser', this.username);
	  	}
	});
	
	Template.followUsers.helpers({  
	  'foundUser': function() {
	    return Session.get('foundUser');
	  },
	   'recommendedUsers': function() {
		//return Session.get('recommendedUsers');
				
		if (Meteor.user()) {
			console.log(Meteor.user().username);
		      var currentFollowings = UserUtils.findFollowings(Meteor.user().username);

		      var recUsers = Meteor.users.find({
			username: {
			  $nin: currentFollowings
			}
		      }, {
			fields: { 'username': 1 },
			limit: 5
		      }).fetch();

		      return recUsers;
		    }
			
		}
		
	});

	
	Template.followUsers.onCreated(function() {  
	  if (Meteor.user()) {
	    this.subscribe('users', Meteor.user().username);
	    this.subscribe('followings', Meteor.user().username);
	  }
	});
	
	Template.tweetFeed.helpers({  
	  'tweetMessage': function() {
	    return Tweets.find({}, { 
		sort: {time: -1}, 
		limit: 10
	    });
	  }
	});m	
	
	Template.tweetFeed.onCreated(function() {  
	  if (Meteor.user()){
	  	this.subscribe('tweets');
	  	this.subscribe('ownTweets', Meteor.user().username);
	  }	
	});	
}

if(Meteor.isServer){
Meteor.methods({  
  'findUser': function(username) {
    return Meteor.users.findOne({
      username: username
    }, {
      fields: { 'username': 1 }
    });
  },

  'followUser' : function(toFollow){
    Relationships.insert({
	follower:Meteor.user().username,
	following:toFollow
    });
  },

  'recommendUsers': function() {
    if (Meteor.user()) {
      var currentFollowings = UserUtils.findFollowings(Meteor.user().username);
      var recUsers = Meteor.users.find({
        username: {
          $nin: currentFollowings
        }
      }, {
        fields: { 'username': 1 },
        limit: 5
      }).fetch();

      return recUsers;
    }
  },
  
  'insertTweet' : function(tweet){	
	if(Meteor.user()){
  		Tweets.insert({message: tweet, user: Meteor.user().username,time:new Date()});
	}
  }
});
  
  Meteor.startup(function () {  
    Relationships._ensureIndex({follower: 1, following: 1}, {unique: 1});
  });

  Meteor.publish('tweets',function(){
		  
	if (this.userId) {
	    var username = Meteor.users.findOne({_id: this.userId}).username;
	    var currentFollowings =  Relationships.find({
				    follower: username
				  }).fetch().map(function(data) {
				    return data.following;
				  });
	    return Tweets.find({user: { $in: currentFollowings }});
	  }
  });

  Meteor.publish('users', function(username) {  
    return Meteor.users.find({}, {
      fields: { 'username': 1 },
      limit: 100
    });
  });

  Meteor.publish('followings', function(username) {  
    return Relationships.find({ follower: username });
  });

  Meteor.publish('followers', function(username) {  
    return Relationships.find({ following: username });
  });

  Meteor.publish('ownTweets', function(username) {  
    return Tweets.find({user: username});
  });


}
