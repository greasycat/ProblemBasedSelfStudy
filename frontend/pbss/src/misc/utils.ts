const capitalizeFirstLetterOfEachWord = (sentence: string) => {
    return sentence
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
}

export { capitalizeFirstLetterOfEachWord };