<script>
  const Stage = {
    BEFORE: 0,
    WORDS: 1,
  };

  let input = $state("What the Segma?");
  let stage = $state(Stage.BEFORE);
  let words = $state(splitWords(input));
  
  function splitWords(text) {
    return text.split(" ")
               .map(word=>word + " ");
  }

  function segment(text) {
    return text.split(" ").map((word)=>word.split(""));
  }

  export function startAnimation(){
    words = splitWords(input);
    console.log(input);
    console.log(words);
    stage = Stage.WORDS;
  }
</script>

<div id=cutting-board>
  {#if stage == Stage.BEFORE}
    <input id=cutting-board-input bind:value={input} />
  {:else if stage == Stage.WORDS}
    <div id="word-container">
      {#each words as word}
        <span class="word">
          {word}
        </span>
      {/each}
    </div>
  {/if}
</div>

<style>
  @import "./style.css";
  
  #cutting-board {
    align-items: center;
    justify-content: center;
    display: flex;
  }

  #word-container {
    width: 100%;
  }

  .word {
    display: inline-block;
    background-color: blue;
  }
</style>
