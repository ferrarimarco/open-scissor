var mongoose = require('mongoose');
var ObjectId = mongoose.Schema.ObjectId;

var schema = mongoose.Schema({
	created: {
		type: Date,
		default: Date.now
	},
	playbook: {
		type: ObjectId,
		ref: 'Playbook'
	},
	name: String,
	play_file: String, //x.yml
	extra_vars: String,
	use_vault: Boolean,
	tmp: false
});

schema.index({
	name: 1
});

module.exports = mongoose.model('Job', schema);
