<script>
  let input = $state("What the Segma?");
  let output = $state("")

  function segment(text) {
    return text.split("");
  }

</script>

<input value={input} style="background: red"/>
<br>
<button onclick={()=>{output = segment(input)}}>
  #mybutton
</button>
<br>
Segmented: {output}

