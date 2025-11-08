<script>
  let input = $state("What the Segma?");
  let output = $state("")

  function segment(text) {
    return text.split(" ").map((word)=>word.split(""));
  }

</script>

<div id=cutting-board>
<input value={input} style="background: red"/>
</div>
<button onclick={()=>{output = segment(input); console.log(segment(input))}}>
  #mybutton
</button>
<br>
Segmented: {output}

