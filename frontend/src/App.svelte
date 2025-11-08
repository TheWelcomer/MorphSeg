<script>
	//variable Init
	let count = $state(0);
	//function to be called on click
	function incrementCount() {
    alert("test")
		//incremtent
		count++
	}
</script>
<!-- the function will be called on click -->
<button onclick={incrementCount}>
	Clicked  {count} {count === 1 ? 'time': 'times'}
</button>
